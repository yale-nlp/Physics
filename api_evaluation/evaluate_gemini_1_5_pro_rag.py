import os
import json
import asyncio
import csv
import statistics
import matplotlib
from tqdm.asyncio import tqdm

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from dotenv import load_dotenv
from openai import AsyncOpenAI
from serpapi import GoogleSearch
import extract_boxed
import equation_equivilancy
import aiofiles

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = AsyncOpenAI(
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    api_key= "Your API Key"
)

SERPAPI_KEY = '3b6f6f97907f74a3e69edcc8f40b983a165f1f3b67dbece3233e7b10de15bea4'  # Consider moving this to your .env file

# ------------------------- Step 1: LLM Generates Google Search Queries -------------------------
async def generate_google_query(question_text, llm="gpt-4o"):
    """Let LLM generate effective Google search queries based on the physics problem."""
    messages = [
        {
            "role": "system",
            "content": "You are a physics expert skilled in using search engines to find relevant information. "
                       "Based on the given physics problem, think about the best way to query Google. "
                       "Generate up to 3 relevant search queries that focus on key concepts, formulas, or theories. "
                       "Avoid searching the entire question; instead, extract essential elements."
        },
        {
            "role": "user",
            "content": f"Generate relevant Google search queries for the following physics problem:\n\n{question_text}"
        }
    ]

    query_suggestions = await ask_llm_with_retries(messages, max_retries=3, llm=llm)
    return query_suggestions.strip() if query_suggestions else "Unable to generate search queries"

# ------------------------- Step 2: Perform Google Search Using SerpAPI -------------------------
async def google_search(query, num_results=3):
    """Use SerpAPI to perform a Google search asynchronously and return relevant summaries."""
    params = {
        "q": query,
        "num": num_results,
        "api_key": SERPAPI_KEY,
        "engine": "google"
    }
    
    loop = asyncio.get_event_loop()
    
    def do_search():
        search = GoogleSearch(params)
        return search.get_dict()
    
    try:
        results = await loop.run_in_executor(None, do_search)
    except Exception as e:
        print(f"SerpAPI request error for query '{query}': {e}")
        return "No relevant information found due to an error."

    snippets = []
    if results and "organic_results" in results:
        for item in results["organic_results"][:num_results]:
            snippet = item.get("snippet")
            if snippet:
                snippets.append(snippet)
    
    if snippets:
        return "\n".join(snippets)
    else:
        return "No relevant information found."

# ------------------------- Step 3: Query LLM with Retries -------------------------
async def ask_llm_with_retries(llm_messages, max_retries=3, delay=2, llm="gpt-4o"):
    """Send request to OpenAI API with a retry mechanism."""
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

# ------------------------- Step 4: Process Each Physics Question -------------------------
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

    # 🔹 Step 1: LLM generates Google search queries
    google_query = await generate_google_query(questions, llm)
    
    # 🔹 Step 2: Perform Google search using generated queries
    search_results = await google_search(google_query, num_results=3)
    
    llm_messages.append({"type": "text", "text": search_results})
    
    llm_final_answers = None
    answers = None
    for attempt in range(max_retries):
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an AI expert specializing in solving advanced physics problems. "
                    "Think step by step and provide a detailed solution and final answer. "
                    "Use relevant information from the search results to support your reasoning process. "
                    "The final answer must be formatted using LaTeX boxed notation: \\[\\boxed{}\\]. "
                    "Example: \\[ \\boxed{ final_answer } \\]"
                )
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

# ------------------------- Step 5: Process the Dataset with Evaluation -------------------------
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

# ------------------------- Step 6: Execute the Main Program -------------------------
async def process_jsonl_list(jsonl_list, base_output_dir, max_lines=1500, llm="gpt-4o", batch_size=16):
    for input_jsonl in jsonl_list:
        jsonl_name = os.path.splitext(os.path.basename(input_jsonl))[0]
        output_dir = os.path.join(base_output_dir, jsonl_name)
        print(f"Starting processing for {input_jsonl}...")
        await process_jsonl(input_jsonl, output_dir, max_lines, llm, batch_size)

def main(llm, base_output_dir, input_jsonl_list, max_lines=1500, batch_size=16):
    asyncio.run(process_jsonl_list(input_jsonl_list, base_output_dir, max_lines, llm, batch_size))

if __name__ == "__main__":
    llm = "gemini-1.5-pro"
    base_output_dir = f"rag_output/{llm}_output"
    input_jsonl_list = [
        # "datasets/atomic_dataset.jsonl",
        # "datasets/electro_dataset.jsonl", 
        # "datasets/mechanics_dataset.jsonl", 
        "datasets/optics_dataset.jsonl",
        # "datasets/quantum_dataset.jsonl", 
        # "datasets/statistics_dataset.jsonl"
    ]
    max_lines = 1500
    batch_size = 16
    main(llm, base_output_dir, input_jsonl_list, max_lines, batch_size)
