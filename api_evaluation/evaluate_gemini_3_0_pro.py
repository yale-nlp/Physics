"""
Gemini 3.0 Pro用評価スクリプト

このスクリプトはGemini 3.0 Proを使用して物理問題の評価を実行します。
最初は5問で検証する設定になっています。
"""

import os
import sys
import json
import csv
import statistics
import asyncio
import matplotlib
from tqdm.asyncio import tqdm

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from dotenv import load_dotenv
from openai import AsyncOpenAI

# 親ディレクトリをパスに追加（extract_boxed, equation_equivilancyをインポートするため）
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import extract_boxed
import equation_equivilancy
import aiofiles

# 環境変数を読み込む
load_dotenv()

# Gemini API用のOpenAI互換クライアントを初期化
# APIキーからコメント部分を除去（#以降を削除）
gemini_api_key = os.getenv("GEMINI_API_KEY")
if gemini_api_key:
    # #以降のコメントを除去
    gemini_api_key = gemini_api_key.split("#")[0].strip()

client = AsyncOpenAI(
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    api_key=gemini_api_key
)

async def ask_llm_with_retries(llm_messages, max_retries=3, delay=2, llm="gemini-3-pro-preview"):
    """
    LLMにリトライ機能付きでリクエストを送信
    
    Gemini 3 Proの推奨設定:
    - reasoning_effort: "medium" (thinking_level "high"にマッピング)
    - temperature: デフォルト1.0を推奨（決定論が必要な場合は0.0も可）
    """
    for attempt in range(max_retries):
        try:
            # Gemini 3 Pro用のパラメータ設定
            # reasoning_effort="medium"はthinking_level="high"にマッピングされる
            create_kwargs = {
                "model": f"{llm}",
                "messages": llm_messages,
                "temperature": 0.0,  # 決定論的な結果が必要な場合は0.0、推奨は1.0
                # "reasoning_effort": "medium",  # 必要に応じてコメントアウト解除
            }
            response = await client.chat.completions.create(**create_kwargs)
            content = response.choices[0].message.content
            if content:
                return content.strip()
            return None
        except Exception as e:
            error_msg = str(e)
            print(f"Attempt {attempt + 1} failed: {error_msg}")
            if attempt < max_retries - 1:
                await asyncio.sleep(delay)
    return None

async def process_entry(entry, llm="gemini-3-pro-preview", max_retries=3):
    """
    1つのエントリを処理して評価結果を返す
    """
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

async def process_jsonl(input_jsonl, output_dir, max_lines=5, llm="gemini-3-pro-preview", batch_size=25):
    """
    JSONLファイルを処理して評価結果を保存
    """
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

    with open(summary_csv, "w", newline="", encoding="utf-8") as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(["Overall Accuracy", "Variance", "Sympy Error Correct Ratio"])
        csv_writer.writerow([overall_accuracy, variance, sympy_error_ratio])

    with open(score_csv, "w", newline="", encoding="utf-8") as scorefile:
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


async def process_jsonl_list(jsonl_list, base_output_dir, max_lines=5, llm="gemini-3-pro-preview"):
    """
    複数のJSONLファイルを順次処理
    """
    for input_jsonl in jsonl_list:
        jsonl_name = os.path.splitext(os.path.basename(input_jsonl))[0]
        output_dir = os.path.join(base_output_dir, jsonl_name)
        print(f"Starting processing for {input_jsonl}...")
        await process_jsonl(input_jsonl, output_dir, max_lines, llm)

def main(llm, base_output_dir, input_jsonl_list, max_lines=5):
    """
    メイン処理関数
    """
    asyncio.run(process_jsonl_list(input_jsonl_list, base_output_dir, max_lines, llm))

if __name__ == "__main__":
    # ==========================================
    # Gemini 3.0 Pro用設定（gemini-3-pro-previewを使用）
    # ==========================================
    llm = "gemini-3-pro-preview"
    base_output_dir = "../outputs/gemini-3.0-pro_output"
    
    # 古典物理学（mechanics）データセット: 221問
    max_lines = 221
    
    # データセットのパス（力学データセットを例として使用）
    # 他のデータセットも同様に追加可能
    input_jsonl_list = [
        "../PHYSICS/mechanics_dataset.jsonl",
        # 他のデータセットを追加する場合は以下をコメントアウト解除
        # "../PHYSICS/atomic_dataset.jsonl",
        # "../PHYSICS/electro_dataset.jsonl",
        # "../PHYSICS/optics_dataset.jsonl",
        # "../PHYSICS/quantum_dataset.jsonl",
        # "../PHYSICS/statistics_dataset.jsonl",
    ]
    
    print("=" * 60)
    print("Gemini 3.0 Pro 評価開始")
    print(f"モデル: {llm}")
    print(f"最大問題数: {max_lines} (テスト用)")
    print(f"出力先: {base_output_dir}")
    print(f"データセット数: {len(input_jsonl_list)}")
    print("=" * 60)
    
    main(llm, base_output_dir, input_jsonl_list, max_lines)
