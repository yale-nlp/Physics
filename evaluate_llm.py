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

def ask_llm_with_retries(llm_messages, max_retries=3, delay=2):
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=llm_messages
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(delay)
    print("All attempts to get a valid response from LLM failed.")
    return None

def process_jsonl_and_generate_answers(input_jsonl, output_jsonl, summary_csv, performance_plot, max_lines=30):
    results = []
    accuracies = []

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
                    "content": "You are an AI expert specializing in answering advanced physics questions. Provide the final answer at the end in Latex boxed format."
                },
                {
                    "role": "user",
                    "content": llm_messages
                }
            ]

            answers = ask_llm_with_retries(messages)
            if answers is None:
                print(f"Skipping entry ID {entry_id} due to repeated failures.")
                continue

            retry_attempts = 3
            for attempt in range(retry_attempts):
                llm_final_answers = extract_boxed.extract_final_answer_allform(answers, answer_type='list')
                if llm_final_answers:
                    break
                print(f"No boxed content found in attempt {attempt + 1}. Retrying...")
                answers = ask_llm_with_retries(messages)
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
                    if equivalency_data.get("final_result", False):
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
    print(f"Overall Accuracy: {overall_accuracy:.2f}, Variance: {variance:.4f}")

    with open(output_jsonl, "w") as outfile:
        for result in results:
            outfile.write(json.dumps(result, ensure_ascii=False) + "\n")

    with open(summary_csv, "w", newline="") as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(["Overall Accuracy", "Variance"])
        csv_writer.writerow([overall_accuracy, variance])

    plt.scatter(range(len(accuracies)), accuracies)
    plt.title("Performance Accuracy Scatter Plot")
    plt.xlabel("Entry Index")
    plt.ylabel("Accuracy")
    plt.savefig(performance_plot)
    plt.show()

    print(f"Results saved to {output_jsonl}, summary to {summary_csv}, and plot to {performance_plot}.")

# Example Usage
category = "mechanics"
input_jsonl = f"{category}_dataset.jsonl"
output_jsonl = f"{category}_llm_response.jsonl"
summary_csv = f"{category}_accuracy.csv"
performance_plot = f"{category}_scatter_plot.png"

process_jsonl_and_generate_answers(input_jsonl, output_jsonl, summary_csv, performance_plot, max_lines=30)
