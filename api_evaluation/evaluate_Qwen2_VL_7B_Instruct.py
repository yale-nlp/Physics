import os
import json
import time
import csv
import statistics
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from dotenv import load_dotenv
from openai import OpenAI
import extract_boxed
import equation_equivilancy

# 加载环境变量
load_dotenv()

# 初始化 OpenAI 客户端
os.environ["OPENAI_BASE_URL"] = "https://api-inference.huggingface.co/v1/"
os.environ["OPENAI_API_KEY"] = os.getenv("HUGGINGFACE_API_KEY")
os.environ["x-wait-for-model"] = "true"
client = OpenAI()

def ask_llm_with_retries(llm_messages, max_retries=3, delay=2, llm="gpt-4o"):
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=f"{llm}",
                messages=llm_messages,
                max_tokens=2048,
                temperature=0.0,
            )
            print(response.choices[0].message.content.strip())
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(delay)
    return None

def process_entry(entry, llm, max_retries=3):
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

    for attempt in range(max_retries):
        messages = [
            {
                "role": "system",
                "content": "You are an AI expert specializing in answering advanced physics questions. Think step by step and provide solution and final answer. Provide the final answer at the end in Latex boxed format \\[boxed{}\\]. Example: \\[ \\boxed{ final_answer} \\]\n"
            },
            {
                "role": "user",
                "content": llm_messages
            }
        ]

        answers = ask_llm_with_retries(messages, max_retries=3, llm=llm)
        if answers is None:
            return None, 0, 0

        llm_final_answers = extract_boxed.extract_final_answer_allform(answers, answer_type='list')
        if llm_final_answers:
            break

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

def process_jsonl_and_generate_answers(input_jsonl, output_dir, max_lines=30, llm="gpt-4o"):
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

    for idx, line in enumerate(lines[:max_lines]):
        data = json.loads(line.strip())
        entry_result = process_entry(data, llm)
        if entry_result[0]:
            results.append(entry_result[0])
            accuracies.append(entry_result[0]["accuracy"])
            sympy_errors_correct_llm_total += entry_result[1]
            sympy_errors_total += entry_result[2]

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

    with open(score_csv, "w", newline="") as scorefile:
        csv_writer = csv.writer(scorefile)
        csv_writer.writerow(["Entry ID", "Accuracy"])
        for idx, accuracy in enumerate(accuracies):
            csv_writer.writerow([results[idx]["id"], accuracy])

    plt.figure()
    plt.scatter(range(len(accuracies)), accuracies, label="Accuracy Scores")
    plt.axhline(overall_accuracy, color="green", linestyle="--", label=f"Mean: {overall_accuracy:.2f}")
    plt.axhline(statistics.median(accuracies), color="blue", linestyle="--", label=f"Median: {statistics.median(accuracies):.2f}")
    plt.axhline(overall_accuracy + statistics.stdev(accuracies), color="red", linestyle="--", label=f"+1 Std Dev: {overall_accuracy + statistics.stdev(accuracies):.2f}")
    plt.axhline(overall_accuracy - statistics.stdev(accuracies), color="red", linestyle="--", label=f"-1 Std Dev: {overall_accuracy - statistics.stdev(accuracies):.2f}")
    plt.title(f"{llm} Performance Plot")
    plt.xlabel("Entry Index")
    plt.ylabel("Correctness")
    plt.legend()
    plt.savefig(performance_plot)

    print(f"Results saved to {output_jsonl}, summary to {summary_csv}, scores to {score_csv}, and plot to {performance_plot}.")

# Example Usage
def main(category, max_lines=5):
    llm = "Qwen/Qwen2-VL-7B-Instruct"
    input_jsonl = f"datasets/{category}_dataset.jsonl"
    output_dir = f"{category}/Qwen2-VL-7B-Instruct_output"

    process_jsonl_and_generate_answers(input_jsonl, output_dir, max_lines, llm)

if __name__ == "__main__":
    category = "mechanics"
    max_lines = 250
    main(category, max_lines)
