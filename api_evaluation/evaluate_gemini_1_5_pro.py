import os
import json
import time
import csv
import statistics
import asyncio
import matplotlib
from tqdm.asyncio import tqdm

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from dotenv import load_dotenv
from openai import AsyncOpenAI
import extract_boxed
import equation_equivilancy
import aiofiles

# 加载环境变量
load_dotenv()

# 初始化 OpenAI 客户端
os.environ["OPENAI_BASE_URL"] = "https://generativelanguage.googleapis.com/v1beta/openai/"
os.environ["OPENAI_API_KEY"] = os.getenv("GEMINI_API_KEY")
client = AsyncOpenAI()

async def ask_llm_with_retries(llm_messages, max_retries=3, delay=2, llm="gpt-4o"):
    for attempt in range(max_retries):
        try:
            response = await client.chat.completions.create(
                model=f"{llm}",
                messages=llm_messages,
                temperature=0.0,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(delay)
    return None

async def process_entry(entry, llm, max_retries=3):
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
        return {
            "id": entry_id,
            "solution": None,
            "final_answers": [],
            "equivalency_results": [],
            "accuracy": 0
        }, 0, 0

    for attempt in range(max_retries):
        messages = [
            {
                "role": "system",
                "content": "You are an AI expert specializing in answering advanced physics questions. Think step by step and provide solution and final answer. Provide the final answer at the end in Latex boxed format \\[\\boxed{}\\]. Example: \\[ \\boxed{ final_answer} \\]"
            },
            {
                "role": "user",
                "content": llm_messages
            }
        ]

        answers = await ask_llm_with_retries(messages, max_retries=3, llm=llm)
        if answers is None:
            return {
                "id": entry_id,
                "solution": None,
                "final_answers": [],
                "equivalency_results": [],
                "accuracy": 0
            }, 0, 0

        llm_final_answers = extract_boxed.extract_final_answer_allform(answers, answer_type='list')
        if llm_final_answers:
            break
    else:
        return {
            "id": entry_id,
            "solution": answers,  # Save raw answers
            "final_answers": [],
            "equivalency_results": [],
            "accuracy": 0  # Mark as failed
        }, 0, 0

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

async def process_jsonl(input_jsonl, output_dir, max_lines=1500, llm="gpt-4o", batch_size=16):
    os.makedirs(output_dir, exist_ok=True)
    output_jsonl = os.path.join(output_dir, "response.jsonl")
    summary_csv = os.path.join(output_dir, "accuracy.csv")
    score_csv = os.path.join(output_dir, "score.csv")
    performance_plot = os.path.join(output_dir, "scatter_plot.png")

    results = []
    accuracies = []
    sympy_errors_correct_llm_total = 0
    sympy_errors_total = 0

    tasks = []
    async with aiofiles.open(input_jsonl, "r") as file:
        async for line in file:
            if len(tasks) >= max_lines:
                break
            data = json.loads(line.strip())
            tasks.append(process_entry(data, llm))

    # Split tasks into batches
    task_batches = [tasks[i:i + batch_size] for i in range(0, len(tasks), batch_size)]

    for batch in tqdm(task_batches, desc=f"Processing {os.path.basename(input_jsonl)} in batches"):
        batch_results = await asyncio.gather(*batch)

        for entry_result in batch_results:
            if entry_result[0]:
                results.append(entry_result[0])
                accuracies.append(entry_result[0]["accuracy"])
                sympy_errors_correct_llm_total += entry_result[1]
                sympy_errors_total += entry_result[2]

    overall_accuracy = sum(accuracies) / len(accuracies) if accuracies else 0.0
    variance = statistics.variance(accuracies) if len(accuracies) > 1 else 0.0
    sympy_error_ratio = sympy_errors_correct_llm_total / sympy_errors_total if sympy_errors_total > 0 else 0.0

    print(f"File: {os.path.basename(input_jsonl)} - Overall Accuracy: {overall_accuracy:.2f}, Variance: {variance:.4f}, Sympy Error Correct Ratio: {sympy_error_ratio:.4f}")

    async with aiofiles.open(output_jsonl, "w") as outfile:
        for result in results:
            await outfile.write(json.dumps(result, ensure_ascii=False) + "\n")

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
    if len(accuracies) > 1:
        plt.axhline(overall_accuracy + statistics.stdev(accuracies), color="red", linestyle="--", label=f"+1 Std Dev: {overall_accuracy + statistics.stdev(accuracies):.2f}")
        plt.axhline(overall_accuracy - statistics.stdev(accuracies), color="red", linestyle="--", label=f"-1 Std Dev: {overall_accuracy - statistics.stdev(accuracies):.2f}")
    plt.title(f"{llm} Performance Plot for {os.path.basename(input_jsonl)}")
    plt.xlabel("Entry Index")
    plt.ylabel("Correctness")
    plt.legend()
    plt.savefig(performance_plot)

    print(f"Results saved to {output_dir}. JSONL: {output_jsonl}, Summary: {summary_csv}, Scores: {score_csv}, Plot: {performance_plot}.")


async def process_jsonl_list(jsonl_list, base_output_dir, max_lines=1500, llm="gpt-4o"):
    for input_jsonl in jsonl_list:
        jsonl_name = os.path.splitext(os.path.basename(input_jsonl))[0]
        output_dir = os.path.join(base_output_dir, jsonl_name)
        print(f"Starting processing for {input_jsonl}...")
        await process_jsonl(input_jsonl, output_dir, max_lines, llm)

def main(llm, base_output_dir, input_jsonl_list, max_lines=1500):
    asyncio.run(process_jsonl_list(input_jsonl_list, base_output_dir, max_lines, llm))

if __name__ == "__main__":
    llm = "gemini-1.5-pro"
    base_output_dir = f"api_output/{llm}_output"
    input_jsonl_list = ["datasets/atomic_dataset.jsonl", "datasets/electro_dataset.jsonl", 
                        "datasets/mechanics_dataset.jsonl", "datasets/optics_dataset.jsonl",
                        "datasets/quantum_dataset.jsonl", "datasets/statistics_dataset.jsonl"]
    max_lines = 1500
    main(llm, base_output_dir, input_jsonl_list, max_lines)
