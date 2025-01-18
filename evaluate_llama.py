import os
import json
import csv
import statistics
import torch
import matplotlib.pyplot as plt
from dotenv import load_dotenv
from vllm import LLM, SamplingParams
import extract_boxed
import equation_equivilancy

# 加载环境变量
load_dotenv()

huggingface_api_key = os.environ.get("HUGGINGFACE_API_KEY")
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

# 检测可用的 GPU 数量
available_gpus = torch.cuda.device_count()
if available_gpus == 0:
    raise RuntimeError("No GPUs found! Please ensure CUDA is properly configured.")

# 设置 tensor_parallel_size 动态分配多卡
tensor_parallel_size = available_gpus

# 登录 Hugging Face
from huggingface_hub import login
login(huggingface_api_key)

torch.cuda.empty_cache()

# 初始化 vLLM 引擎（使用 Llama 模型）
engine = LLM(
    model="meta-llama/Llama-3.1-8B-Instruct",  # 替换为本地 Llama 模型路径
    tensor_parallel_size=1,  # 根据硬件支持设置并行度
    dtype="half",
    kv_cache_dtype="fp8",
    max_model_len=4096,
    download_dir='/scratch/kf2365/.cache/huggingface',
)

print('engine loaded')
os.system("nvidia-smi")

def ask_llm_with_retries(llm_messages, max_retries=3, delay=2):
    """同步运行 vLLM 模型推理，支持多次重试"""
    for attempt in range(max_retries):
        try:
            # 提取用户消息
            sampling_params = SamplingParams(temperature=0, max_tokens=2048, repetition_penalty=1.2)
            
            # 使用 vLLM 进行推理
            outputs = engine.chat(llm_messages, sampling_params)
            response = ""
            for output in outputs:
                generated_text = output.outputs[0].text
                response += generated_text + "\n"
                            
            print(response)
            
            return response
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                torch.cuda.empty_cache()
    print("All attempts to get a valid response from vLLM failed.")
    return None

def process_entry(entry, max_retries=3):
    entry_id = entry.get("id")
    questions = entry.get("questions", "")
    graphs = entry.get("graphs", [])
    dataset_answers = entry.get("final_answers", [])

    llm_messages = []
    if questions:
        llm_messages.append({"type": "text", "text": questions})
    if graphs:
        llm_messages.extend(graphs)
    if not llm_messages:
        return None, 0, 0

    print(f"Processing entry ID: {entry_id}...")

    for attempt in range(max_retries):
        messages = [
            {
                "role": "system",
                "content": "You are an AI expert specializing in answering advanced physics questions. Think step by step and provide solution and final answer. Provide the final answer at the end in Latex boxed format \\[boxed{}\\]. Example: \\[ \\boxed{ final_answer} \\\]]\n"
            },
            {
                "role": "user",
                "content": llm_messages
            }
        ]
    
        answers = ask_llm_with_retries(messages, max_retries=max_retries)
        if answers is None:
            print(f"Skipping entry ID {entry_id} due to repeated failures.")
            return None, 0, 0

        llm_final_answers = extract_boxed.extract_final_answer_allform(answers, answer_type='list')
        if llm_final_answers:
            break
        
        print(f"Attempt {attempt + 1}: No valid boxed content. Retrying...")
    
    if not llm_final_answers:
        print(f"Skipping entry ID {entry_id} due to missing boxed content after {max_retries} attempts.")
        return None, 0, 0
    

    flattened_answers = [item for sublist in llm_final_answers for item in sublist] if isinstance(llm_final_answers[0], list) else llm_final_answers
    equivalency_results = []
    correct_count = 0
    sympy_errors_correct_llm = 0
    sympy_errors = 0

    for llm_answer in flattened_answers:
        matched = False
        for dataset_answer in dataset_answers:
            equivalency_data = equation_equivilancy.is_equiv(llm_answer, dataset_answer, verbose=False)
            equivalency_results.append(equivalency_data)

            sympy_result = equivalency_data.get("sympy_result")
            llm_result = equivalency_data.get("llm_result")

            if sympy_result is False and llm_result is True:
                sympy_errors_correct_llm += 1
            if sympy_result is not None:
                sympy_errors += 1

            if equivalency_data.get("final_result") == True:
                correct_count += 1
                matched = True
                break
        if matched:
            continue

    total_comparisons = len(flattened_answers)
    accuracy = correct_count / total_comparisons if total_comparisons > 0 else 0.0


    return {
        "id": entry_id,
        "solution": answers,
        "final_answers": flattened_answers,
        "equivalency_results": equivalency_results,
        "accuracy": accuracy
    }, sympy_errors_correct_llm, sympy_errors

def process_jsonl_and_generate_answers(input_jsonl, output_dir, max_lines=30):
    os.makedirs(output_dir, exist_ok=True)
    output_jsonl = os.path.join(output_dir, "response.jsonl")
    summary_csv = os.path.join(output_dir, "accuracy.csv")
    score_csv = os.path.join(output_dir, "score.csv")
    performance_plot = os.path.join(output_dir, "scatter_plot.png")

    results = []
    accuracies = []
    sympy_errors_correct_llm_total = 0
    sympy_errors_total = 0

    with open(input_jsonl, "r") as file:
        lines = file.readlines()

    for idx, line in enumerate(lines):
        if idx >= max_lines:
            break
        data = json.loads(line.strip())

        # 逐一运行任务
        entry_result = process_entry(data)
        if entry_result[0]:
            results.append(entry_result[0])
            accuracies.append(entry_result[0]["accuracy"])
            sympy_errors_correct_llm_total += entry_result[1]
            sympy_errors_total += entry_result[2]

        # 清理显存
        torch.cuda.empty_cache()

    overall_accuracy = sum(accuracies) / len(accuracies) if accuracies else 0.0
    variance = statistics.variance(accuracies) if len(accuracies) > 1 else 0.0
    sympy_error_ratio = sympy_errors_correct_llm_total / sympy_errors_total if sympy_errors_total > 0 else 0.0

    print(f"Overall Accuracy: {overall_accuracy:.2f}, Variance: {variance:.4f}, Sympy Error Correct Ratio: {sympy_error_ratio:.4f}")

    # 保存结果到 JSONL 文件
    with open(output_jsonl, "w") as outfile:
        for result in results:
            json.dump(result, outfile, ensure_ascii=False)
            outfile.write("\n")

    # 保存摘要和分数到 CSV 文件
    with open(summary_csv, "w", newline="") as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(["Overall Accuracy", "Variance", "Sympy Error Correct Ratio"])
        csv_writer.writerow([overall_accuracy, variance, sympy_error_ratio])

    with open(score_csv, "w", newline="") as scorefile:
        csv_writer = csv.writer(scorefile)
        csv_writer.writerow(["Entry ID", "Accuracy"])
        for idx, accuracy in enumerate(accuracies):
            csv_writer.writerow([results[idx]["id"], accuracy])

    # 绘制性能图
    plt.figure()
    plt.scatter(range(len(accuracies)), accuracies, label="Accuracy Scores")
    plt.axhline(overall_accuracy, color="green", linestyle="--", label=f"Mean: {overall_accuracy:.2f}")
    plt.axhline(statistics.median(accuracies), color="blue", linestyle="--", label=f"Median: {statistics.median(accuracies):.2f}")
    plt.axhline(overall_accuracy + statistics.stdev(accuracies), color="red", linestyle="--", label=f"+1 Std Dev: {overall_accuracy + statistics.stdev(accuracies):.2f}")
    plt.axhline(overall_accuracy - statistics.stdev(accuracies), color="red", linestyle="--", label=f"-1 Std Dev: {overall_accuracy - statistics.stdev(accuracies):.2f}")
    plt.title("vLLM Performance Plot")
    plt.xlabel("Entry Index")
    plt.ylabel("Correctness")
    plt.legend()
    plt.savefig(performance_plot)

    plt.close()  # 关闭 Matplotlib 图形
    torch.cuda.empty_cache()  # 清理显存

    print(f"Results saved to {output_jsonl}, summary to {summary_csv}, scores to {score_csv}, and plot to {performance_plot}.")


# Example Usage
if __name__ == "__main__":
    category = "mechanics"
    input_jsonl = f"PHYSICS/mechanics_dataset_textonly.jsonl"
    output_dir = f"PHYSICS/{category}_vllm_output"

    print(f"Detected {available_gpus} GPUs. Using tensor_parallel_size = {tensor_parallel_size}.")
    process_jsonl_and_generate_answers(input_jsonl, output_dir, max_lines=5)
