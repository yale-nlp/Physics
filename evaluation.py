import os
import json
import csv
import multiprocessing
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor, as_completed, TimeoutError
import extract_boxed
import equation_equivilancy

# 解决 MacOS 进程池问题
if __name__ == "__main__":
    multiprocessing.set_start_method("forkserver")

class VLLMPhysicsEvaluator:
    def __init__(self, base_output_dir, dataset_dir, num_workers=2, timeout=30):
        self.base_output_dir = base_output_dir
        self.dataset_dir = dataset_dir
        self.num_workers = num_workers
        self.timeout = timeout

    def evaluate_entry(self, entry):
        """评估单条数据的函数，增加错误处理，防止进程崩溃。"""
        try:
            gen_data, dataset_data = entry
            entry_id = gen_data.get("id")
            llm_answers = gen_data.get("llm_answers")
            dataset_answers = dataset_data.get("final_answers", [])

            # 提取 LLM 的最终答案
            llm_final_answers = extract_boxed.extract_final_answer_allform(llm_answers, answer_type='list')

            if not llm_final_answers:
                flattened_answers = []
            else:
                flattened_answers = (
                    [item for sublist in llm_final_answers for item in sublist]
                    if isinstance(llm_final_answers[0], list)
                    else llm_final_answers
                )

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
                "solution": llm_answers,
                "final_answers": flattened_answers,
                "equivalency_results": equivalency_results,
                "accuracy": accuracy
            }, sympy_errors_correct_llm, sympy_errors

        except Exception as e:
            print(f"Error processing entry: {e}")
            return {
                "id": "error",
                "solution": None,
                "final_answers": [],
                "equivalency_results": [],
                "accuracy": 0  # 失败时准确率设为 0
            }, 0, 0

    def process_single_dataset(self, llm_folder, dataset_folder):
        dataset_output_path = os.path.join(self.base_output_dir, llm_folder, dataset_folder)
        response_file = os.path.join(dataset_output_path, "response.jsonl")

        if not os.path.exists(response_file):
            print(f"Skipping {dataset_folder} in {llm_folder}: response.jsonl not found.")
            return

        dataset_file = os.path.join(self.dataset_dir, f"{dataset_folder}.jsonl")
        if not os.path.exists(dataset_file):
            print(f"Skipping {dataset_folder} in {llm_folder}: Corresponding dataset not found.")
            return

        output_jsonl = os.path.join(dataset_output_path, "final_evaluation.jsonl")
        summary_csv = os.path.join(dataset_output_path, "accuracy.csv")

        try:
            with open(response_file, "r") as gen_file, open(dataset_file, "r") as dataset_file:
                gen_lines = [json.loads(line.strip()) for line in gen_file]
                dataset_lines = [json.loads(line.strip()) for line in dataset_file]

            entries = list(zip(gen_lines, dataset_lines))
            results = []
            accuracies = []

            with ProcessPoolExecutor(max_workers=self.num_workers) as executor:
                futures = {executor.submit(self.evaluate_entry, entry): entry for entry in entries}
                
                for future in tqdm(as_completed(futures), total=len(futures), desc=f"Evaluating {llm_folder}/{dataset_folder}"):
                    try:
                        result, _, _ = future.result(timeout=self.timeout)
                    except TimeoutError:
                        print(f"Timeout error on dataset {dataset_folder} in {llm_folder}")
                        result = {"id": "timeout_error", "accuracy": 0}
                    except Exception as e:
                        print(f"Error processing {dataset_folder} in {llm_folder}: {e}")
                        result = {"id": "error", "accuracy": 0}

                    results.append(result)
                    accuracies.append(result["accuracy"])

            overall_accuracy = sum(accuracies) / len(accuracies) if accuracies else 0.0

            with open(output_jsonl, "w") as outfile:
                for result in results:
                    json.dump(result, outfile, ensure_ascii=False)
                    outfile.write("\n")

            with open(summary_csv, "w", newline="") as csvfile:
                csv_writer = csv.writer(csvfile)
                csv_writer.writerow(["Overall Accuracy"])
                csv_writer.writerow([overall_accuracy])

            print(f"Evaluation complete for {llm_folder}/{dataset_folder}. Results saved in {dataset_output_path}")

        except Exception as e:
            print(f"Critical error processing {dataset_folder} in {llm_folder}: {e}")

    def process_all_llm_outputs(self):
        """遍历 base_output_dir 目录，批量处理所有 LLM 生成的 response.jsonl 文件。"""
        for llm_folder in os.listdir(self.base_output_dir):
            llm_path = os.path.join(self.base_output_dir, llm_folder)
            if not os.path.isdir(llm_path):
                continue  # 跳过非目录项

            for dataset_folder in os.listdir(llm_path):
                dataset_path = os.path.join(llm_path, dataset_folder)
                if not os.path.isdir(dataset_path):
                    continue  # 跳过非目录项
                self.process_single_dataset(llm_folder, dataset_folder)  # 串行处理每个数据集




if __name__ == "__main__":
    evaluator = VLLMPhysicsEvaluator(
        base_output_dir="offline_outputs",
        dataset_dir="datasets",
        num_workers=4,
        timeout=60
    )
    evaluator.process_all_llm_outputs()
