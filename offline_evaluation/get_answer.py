import os
import json
import torch
import sys
import atexit
import traceback
from tqdm import tqdm
from vllm import LLM, SamplingParams
import argparse


class VLLMPhysicsPipeline:
    def __init__(self, model_name, download_dir, output_dir, max_lines=30):
        self.model_name = model_name
        self.download_dir = download_dir
        self.output_dir = output_dir
        self.max_lines = max_lines
        

        # Initialize vLLM engine
        if 'Deepseek-V2' in model_name:
            self.engine = LLM(
                model=self.model_name,
                tensor_parallel_size=torch.cuda.device_count(),
                kv_cache_dtype="auto",
                hf_overrides={"architectures": ["DeepseekVLV2ForCausalLM"]},
                download_dir=self.download_dir,
            )
        if 'Baichuan' in model_name:
            self.engine = LLM(
                model=self.model_name,
                tensor_parallel_size=torch.cuda.device_count(),
                kv_cache_dtype="auto",
                hf_overrides={"architectures": ["BaiChuanForCausalLM"]},
                download_dir=self.download_dir,
                trust_remote_code=True,
            )
        # elif ('awq' in model_name) or ('AWQ' in model_name):
        #     self.engine = LLM(
        #         model=self.model_name,
        #         tensor_parallel_size=torch.cuda.device_count(),
        #         kv_cache_dtype="auto",
        #         download_dir=self.download_dir,
        #         trust_remote_code=True,
        #         quantization= 'awq',
        #         dtype = 'half',
        #     )
        if ('Llama-3.2-11B-Vision') in model_name:
            # Special handling for Llama-3.2-11B-Vision-Instruct-bnb-4bit
            self.engine = LLM(
                model=self.model_name,
                kv_cache_dtype="auto",
                max_model_len=4096,
                max_num_seqs=2,
                download_dir=self.download_dir,
                enforce_eager=True,
                trust_remote_code=True,
                pipeline_parallel_size=2,
            )
        if ('mistral') in model_name:
            self.engine = LLM(
                model=self.model_name,
                tensor_parallel_size=torch.cuda.device_count(),
                kv_cache_dtype="auto",
                max_model_len=4096,
                download_dir=self.download_dir,
                trust_remote_code=True,
                tokenizer_mode='mistral',
            )
            
        else:
            self.engine = LLM(
                model=self.model_name,
                tensor_parallel_size=torch.cuda.device_count(),
                kv_cache_dtype="auto",
                # max_model_len=8192,
                download_dir=self.download_dir,
                trust_remote_code=True,
            )
        
        
        print("vLLM engine initialized.")

    def ask_llm_with_retries(self, llm_messages_batch, max_retries=3):
        """
        Run vLLM inference in batch mode with retries.

        Parameters:
            llm_messages_batch (list): A list of messages for batch inference.
            max_retries (int): Number of retries for handling failures.

        Returns:
            list: A list of responses from the model for the batch.
        """
        for attempt in range(max_retries):
            try:
                sampling_params = SamplingParams(
                    temperature=0,
                    max_tokens=8192,
                    repetition_penalty=1.2,
                )
                outputs = self.engine.chat(
                    llm_messages_batch, 
                    sampling_params,
                )
                responses = [output.outputs[0].text for output in outputs]
                return responses
            except Exception as e:
                print(f"Batch attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    torch.cuda.empty_cache()
        print("All attempts to get valid responses from vLLM failed.")
        return [None] * len(llm_messages_batch)

    def process_jsonl(self, dataset_path):
        dataset_name = os.path.splitext(os.path.basename(dataset_path))[0]
        dataset_output_dir = os.path.join(self.output_dir, dataset_name)
        os.makedirs(dataset_output_dir, exist_ok=True)

        output_jsonl = os.path.join(dataset_output_dir, "response.jsonl")

        with open(dataset_path, "r") as file:
            lines = file.readlines()

        # 1) 收集所有数据（或按 max_lines 限制）
        all_data = []
        for idx, line in enumerate(lines):
            if idx >= self.max_lines:
                break
            data = json.loads(line.strip())
            all_data.append(data)

        # 2) 构建发送给 vLLM 的批量消息
        llm_messages_batch = []
        results = []

        for entry in tqdm(all_data, desc=f"Processing {dataset_name}"):
            entry_id = entry.get("id")
            questions = entry.get("questions", "")
            graphs = entry.get("graphs", [])

            # 构造要发送给 LLM 的对话内容
            user_content = []
            if questions:
                user_content.append({"type": "text", "text": questions})
            if graphs:
                user_content.append(graphs[0])

            llm_messages_batch.append([
                {
                    "role": "system",
                    "content": (
                        "You are an AI expert specializing in answering advanced physics questions. "
                        "Think step by step and provide solution and final answer. "
                        "Provide the final answer at the end in Latex boxed format \\[\\boxed{}\\]."
                        "Example: \\[ \\boxed{ final_answer} \\]"
                    ),
                },
                {"role": "user", "content": user_content},
            ])

        # 3) 执行批量推理（vLLM 内部自动进行动态批处理）
        responses = self.ask_llm_with_retries(llm_messages_batch)

        # 4) 将推理结果与原始输入对应起来并输出
        for entry, answer in zip(all_data, responses):
            result = {
                "id": entry.get("id"),
                "questions": entry.get("questions", ""),
                "graphs": entry.get("graphs", []),
                "llm_answers": answer,
            }
            results.append(result)

        # 5) 将结果写回到 JSONL 文件
        with open(output_jsonl, "w", encoding="utf-8") as outfile:
            for result in results:
                json.dump(result, outfile, ensure_ascii=False)
                outfile.write("\n")

        print(f"Results for dataset {dataset_name} saved to {output_jsonl}.")

    def process_jsonl_list(self, dataset_list):
        for dataset_path in dataset_list:
            print(f"Processing dataset: {dataset_path}")
            self.process_jsonl(dataset_path)


def cleanup_gpu():
    """Function to clear GPU memory."""
    try:
        print("Releasing GPU memory...")
        torch.cuda.empty_cache()
        print("GPU memory released successfully.")
    except Exception as e:
        print(f"Failed to release GPU memory: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run vLLM Physics Pipeline.")
    parser.add_argument("--model_name", type=str, required=True, help="Name of the model to use.")
    parser.add_argument("--download_dir", type=str, required=True, help="Directory to cache downloaded model files.")
    parser.add_argument("--output_dir", type=str, required=True, help="Directory to save output results.")
    parser.add_argument("--dataset_list", type=str, nargs='+', required=True, help="List of paths to input JSONL datasets.")
    parser.add_argument("--max_lines", type=int, default=30, help="Maximum number of lines to process from each dataset.")

    args = parser.parse_args()

    atexit.register(cleanup_gpu)

    try:
        pipeline = VLLMPhysicsPipeline(
            model_name=args.model_name,
            download_dir=args.download_dir,
            output_dir=args.output_dir,
            max_lines=args.max_lines,
        )

        pipeline.process_jsonl_list(args.dataset_list)

    except Exception as e:
        print("An error occurred:", e)
        traceback.print_exc()
        sys.exit(1)

    finally:
        cleanup_gpu()
