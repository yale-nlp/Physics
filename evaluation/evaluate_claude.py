import os
import json
import time
import csv
import statistics
import matplotlib.pyplot as plt
from dotenv import load_dotenv
from openai import OpenAI
import extract_boxed
import equation_equivilancy

# 加载环境变量
load_dotenv()

# 初始化 OpenAI 客户端
os.environ["OPENAI_BASE_URL"] = "https://yanlp.zeabur.app/v1"
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
client = OpenAI()

def ask_llm_with_retries(llm_messages, max_retries=3, delay=2, llm="gpt-4o"):
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=f"{llm}",
                messages=llm_messages
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(delay)
    print("All attempts to get a valid response from LLM failed.")
    return None

def process_jsonl_and_generate_answers(input_jsonl, output_jsonl, summary_csv, performance_plot, score_csv, max_lines=30, llm="gpt-4o"):
    results = []
    accuracies = []

    # 初始化统计变量
    sympy_errors_correct_llm_total = 0
    sympy_errors_total = 0

    # Read JSONL file
    with open(input_jsonl, "r") as file:
        for idx, line in enumerate(file):
            if idx >= max_lines:
                break

            data = json.loads(line.strip())
            entry_id = data.get("id")
            questions = data.get("questions", "")
            graphs = data.get("graphs", [])
            dataset_answers = data.get("final_answers", [])

            llm_messages = []
            if questions:
                llm_messages.append({"type": "text", "text": questions})
            if graphs:
                llm_messages.extend(graphs)
            if not llm_messages:
                continue

            print(f"Processing entry ID: {entry_id}...")

            messages = [
                {
                    "role": "system",
                    "content": "You are an AI expert specializing in answering advanced physics questions. Think step by step and provide solution and final answer. Provide the final answer at the end in Latex boxed format \\[boxed{}\\]. Example: \\[ \\boxed{ final_answer} \\]]\n"
                },
                {
                    "role": "user",
                    "content": llm_messages
                }
            ]

            answers = ask_llm_with_retries(messages, max_retries=3, llm=llm)
            if answers is None:
                print(f"Skipping entry ID {entry_id} due to repeated failures.")
                continue

            retry_attempts = 3
            for attempt in range(retry_attempts):
                llm_final_answers = extract_boxed.extract_final_answer_allform(answers, answer_type='list')
                if llm_final_answers:
                    break
                print(f"No boxed content found in attempt {attempt + 1}. Retrying...")
                answers = ask_llm_with_retries(messages, llm=llm)
                if answers is None:
                    break

            if not llm_final_answers:
                print(f"Skipping entry ID {entry_id} due to missing boxed content after retries.")
                continue

            flattened_answers = [item for sublist in llm_final_answers for item in sublist] if isinstance(llm_final_answers[0], list) else llm_final_answers
            equivalency_results = []
            correct_count = 0

            for llm_answer in flattened_answers:
                matched = False
                for dataset_answer in dataset_answers:
                    equivalency_data = equation_equivilancy.is_equiv(llm_answer, dataset_answer, verbose=False)
                    equivalency_results.append(equivalency_data)

                    # 判断是否是 sympy 错误但 LLM 正确的情况
                    sympy_result = equivalency_data.get("sympy_result")
                    llm_result = equivalency_data.get("llm_result")
                    final_result = equivalency_data.get("final_result")

                    if sympy_result is False and llm_result is True:
                        sympy_errors_correct_llm_total += 1
                    if sympy_result is not None:
                        sympy_errors_total += 1

                    if final_result == True: 
                        correct_count += 1
                        matched = True
                        break
                if matched:
                    continue

            total_comparisons = len(flattened_answers)
            accuracy = correct_count / total_comparisons if total_comparisons > 0 else 0.0
            accuracies.append(accuracy)

            results.append({
                "id": entry_id,
                "solution": answers,
                "final_answers": flattened_answers,
                "equivalency_results": equivalency_results,
                "accuracy": accuracy
            })

            print(f"Answers processed for entry ID {entry_id}. Accuracy: {accuracy:.2f}")

    overall_accuracy = sum(accuracies) / len(accuracies) if accuracies else 0.0
    variance = statistics.variance(accuracies) if len(accuracies) > 1 else 0.0
    sympy_error_ratio = sympy_errors_correct_llm_total / sympy_errors_total if sympy_errors_total > 0 else 0.0

    print(f"Overall Accuracy: {overall_accuracy:.2f}, Variance: {variance:.4f}, Sympy Error Correct Ratio: {sympy_error_ratio:.4f}")

    with open(output_jsonl, "w") as outfile:
        for result in results:
            outfile.write(json.dumps(result, ensure_ascii=False) + "\n")

    with open(summary_csv, "w", newline="") as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(["Overall Accuracy", "Variance", "Sympy Error Correct Ratio"])
        csv_writer.writerow([overall_accuracy, variance, sympy_error_ratio])

    # 保存每个问题的分数到单独的 CSV 文件
    with open(score_csv, "w", newline="") as scorefile:
        csv_writer = csv.writer(scorefile)
        csv_writer.writerow(["Entry ID", "Accuracy"])
        for idx, accuracy in enumerate(accuracies):
            csv_writer.writerow([results[idx]["id"], accuracy])

    # 绘制一维散点图并标注统计数据
    plt.figure()
    plt.scatter(range(len(accuracies)), accuracies, label="Accuracy Scores")
    plt.axhline(overall_accuracy, color="green", linestyle="--", label=f"Mean: {overall_accuracy:.2f}")
    plt.axhline(statistics.median(accuracies), color="blue", linestyle="--", label=f"Median: {statistics.median(accuracies):.2f}")
    plt.axhline(overall_accuracy + statistics.stdev(accuracies), color="red", linestyle="--", label=f"+1 Std Dev: {overall_accuracy + statistics.stdev(accuracies):.2f}")
    plt.axhline(overall_accuracy - statistics.stdev(accuracies), color="red", linestyle="--", label=f"-1 Std Dev: {overall_accuracy - statistics.stdev(accuracies):.2f}")
    plt.title(f"{llm}Performance Plot")
    plt.xlabel("Entry Index")
    plt.ylabel("Correctness")
    plt.legend()
    plt.savefig(performance_plot)
    plt.show()

    print(f"Results saved to {output_jsonl}, summary to {summary_csv}, scores to {score_csv}, and plot to {performance_plot}.")

# Example Usage
category = "mechanics"
llm = "claude-3-5-sonnet-20241022"
input_jsonl = f"{category}_dataset.jsonl"
output_jsonl = f"{category}_claude_response.jsonl"
summary_csv = f"{category}_claude_accuracy.csv"
score_csv = f"{category}_claude_score.csv"
performance_plot = f"{category}_claude_scatter_plot.png"

process_jsonl_and_generate_answers(input_jsonl, output_jsonl, summary_csv, performance_plot, score_csv, max_lines=50, llm=llm)
