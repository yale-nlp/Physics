"""
力学データセット専用評価スクリプト（GPT-5.2、reasoningパラメータなし版）

このスクリプトは力学（mechanics）データセットのみを対象にGPT-5.2で評価を実行します。
reasoningパラメータなし版で、比較用に使用します。
"""

from __future__ import annotations

import os
import sys
import json
import asyncio
import csv
import statistics
import matplotlib
from dataclasses import dataclass
from typing import Any
from tqdm.asyncio import tqdm
from tqdm import tqdm as tqdm_sync

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from dotenv import load_dotenv
from openai import AsyncOpenAI

# 親ディレクトリをパスに追加（extract_boxed, equation_equivilancyをインポートするため）
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import extract_boxed
import equation_equivilancy
import aiofiles

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = AsyncOpenAI(
    base_url="https://api.openai.com/v1",
    api_key=os.getenv("OPENAI_API_KEY")
)

@dataclass(frozen=True)
class LLMCallResult:
    content: str | None
    usage: dict[str, Any] | None


def _convert_to_responses_input(llm_messages: list[dict[str, Any]]) -> str | list[dict[str, Any]]:
    """
    Chat Completions形式のメッセージをResponses APIのinput形式に変換する。
    
    - 画像がない場合は文字列形式を返す（シンプルで高速）
    - 画像がある場合はmessage形式に変換する
    """
    has_images = any(msg.get("type") == "image_url" for msg in llm_messages)
    
    if not has_images:
        # 画像がない場合は文字列形式（シンプル）
        text_parts = []
        for msg in llm_messages:
            if msg.get("type") == "text":
                text_parts.append(msg.get("text", ""))
        return "\n".join(text_parts)
    else:
        # 画像がある場合はmessage形式に変換
        content_items = []
        for msg in llm_messages:
            if msg.get("type") == "text":
                content_items.append({
                    "type": "input_text",
                    "text": msg.get("text", "")
                })
            elif msg.get("type") == "image_url":
                image_url = msg.get("image_url", {})
                if isinstance(image_url, dict):
                    url = image_url.get("url", "")
                    if url.startswith("data:image"):
                        # base64形式の画像データ
                        content_items.append({
                            "type": "input_image",
                            "source": {
                                "type": "base64",
                                "media_type": url.split(";")[0].split(":")[1],
                                "data": url.split(",")[1] if "," in url else ""
                            }
                        })
        
        return [{
            "type": "message",
            "role": "user",
            "content": content_items
        }]


async def ask_llm_with_retries(
    llm_messages: list[dict[str, Any]],
    *,
    max_retries: int = 3,
    delay: int = 2,
    llm: str = "gpt-5.2",
    max_output_tokens: int | None = None,
) -> LLMCallResult:
    """
    OpenAI Responses APIを使用してGPT-5.2を呼び出す（reasoningパラメータなし版）。
    
    - **注意**: 画像入力（data:image のbase64直埋め）はプロンプトが巨大になりやすい。
      そのため「抽出失敗で同じ入力を再送」しないよう、上位層で再送回数を抑制する。
    - responses APIでは`input`パラメータにメッセージを渡す
    """
    # メッセージをresponses API形式に変換
    input_data = _convert_to_responses_input(llm_messages)
    
    for attempt in range(max_retries):
        try:
            # responses.create()エンドポイントを使用（reasoningパラメータなし）
            create_kwargs: dict[str, Any] = {
                "model": llm,
                # reasoningパラメータを設定しない（比較用）
                "input": input_data,  # responses APIではinputパラメータを使用
            }
            if max_output_tokens is not None:
                create_kwargs["max_output_tokens"] = max_output_tokens
            
            response = await client.responses.create(**create_kwargs)
            
            # responses APIのレスポンス形式に合わせて処理
            content = response.output_text if hasattr(response, 'output_text') else None
            
            # usage情報の取得
            usage = None
            if hasattr(response, 'usage') and response.usage:
                usage = {
                    "prompt_tokens": getattr(response.usage, 'prompt_tokens', 0),
                    "completion_tokens": getattr(response.usage, 'completion_tokens', 0),
                    "total_tokens": getattr(response.usage, 'total_tokens', 0),
                }
            
            return LLMCallResult(content.strip() if content else None, usage)
        except Exception as e:
            error_str = str(e)
            print(f"Attempt {attempt + 1} failed: {e}")
            
            # 429エラー（クォータ超過）の場合は、より長い待機時間を設定
            if "429" in error_str or "insufficient_quota" in error_str.lower():
                if attempt < max_retries - 1:
                    # 429エラーの場合は指数バックオフ: 10秒 → 20秒 → 40秒
                    wait_time = 10 * (2 ** attempt)
                    print(f"Quota error detected. Waiting {wait_time} seconds before retry...")
                    await asyncio.sleep(wait_time)
                else:
                    print("Max retries reached. API quota exceeded. Please check your billing.")
            elif attempt < max_retries - 1:
                await asyncio.sleep(delay)
    return LLMCallResult(None, None)


def _merge_usage(usages: list[dict[str, Any]]) -> dict[str, int]:
    merged = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    for u in usages:
        for k in merged:
            v = u.get(k)
            if isinstance(v, int):
                merged[k] += v
    return merged


def _extract_boxed_list(answer_text: str | None) -> list[str]:
    if not answer_text:
        return []
    extracted = extract_boxed.extract_final_answer_allform(answer_text, answer_type="list")
    if not extracted:
        return []
    if isinstance(extracted[0], list):
        return [item for sublist in extracted for item in sublist]
    return extracted

async def process_entry(
    entry: dict[str, Any],
    llm: str,
    *,
    solve_attempts: int = 1,
    api_retries: int = 3,
    format_attempts: int = 2,
    format_max_output_tokens: int = 256,
) -> tuple[dict[str, Any], int, int]:
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
            "accuracy": 0,
            "token_usage": None,
        }, 0, 0

    system_prompt = (
        "You are an AI expert specializing in answering advanced physics questions. "
        "Think step by step and provide solution and final answer. "
        "IMPORTANT: Do NOT use \\boxed{} format in intermediate steps or calculations. "
        "Only use \\boxed{} format ONCE at the very end for the final answer. "
        "Provide the final answer at the end in Latex boxed format \\[\\boxed{}\\]. "
        "Example: \\[ \\boxed{ final_answer} \\]"
    )

    # 1) まずは「解く」(画像がある場合、ここが最も高コスト)
    solve_usages: list[dict[str, Any]] = []
    answers: str | None = None
    flattened_answers: list[str] = []

    for _ in range(max(1, solve_attempts)):
        # responses API用にinput形式に変換
        # システムプロンプトとユーザーメッセージを結合
        input_messages = []
        # システムプロンプトを先頭に追加（responses APIではinputに含める）
        if system_prompt:
            input_messages.append({"type": "text", "text": system_prompt})
        # ユーザーメッセージ（テキストと画像）を追加
        input_messages.extend(llm_messages)
        
        solve_result = await ask_llm_with_retries(
            input_messages,
            max_retries=api_retries,
            llm=llm,
        )
        answers = solve_result.content
        if solve_result.usage:
            solve_usages.append(solve_result.usage)
        if answers is None:
            return {
                "id": entry_id,
                "solution": None,
                "final_answers": [],
                "equivalency_results": [],
                "accuracy": 0,
                "token_usage": _merge_usage(solve_usages) if solve_usages else None,
            }, 0, 0

        flattened_answers = _extract_boxed_list(answers)
        if flattened_answers:
            break

        # 2) boxed抽出に失敗した場合、同じ巨大入力を再送せず「回答の整形」だけを依頼する
        #    これにより data:image(base64) を再送しない＝無駄トークンを大きく削減できる。
        for _ in range(format_attempts):
            # responses API用にinput形式に変換（画像なしなので文字列形式）
            format_system_prompt = (
                "You are a careful formatter. "
                "Extract ONLY the final answer from the given text and output it in LaTeX boxed format "
                "\\[\\boxed{...}\\]. Output ONLY the boxed answer, nothing else."
            )
            format_user_content = (
                "Text:\n"
                "-----\n"
                f"{answers}\n"
                "-----\n"
                "Return ONLY the boxed final answer."
            )
            format_messages = [
                {"type": "text", "text": format_system_prompt},
                {"type": "text", "text": format_user_content},
            ]
            format_result = await ask_llm_with_retries(
                format_messages,
                max_retries=api_retries,
                llm=llm,
                max_output_tokens=format_max_output_tokens,
            )
            if format_result.usage:
                solve_usages.append(format_result.usage)
            if format_result.content:
                flattened_answers = _extract_boxed_list(format_result.content)
                if flattened_answers:
                    # 保存するsolutionは「解いた本文」を優先（評価の再現性のため）
                    break
        if flattened_answers:
            break

    if not flattened_answers:
        return {
            "id": entry_id,
            "solution": answers,  # Save raw answers
            "final_answers": [],
            "equivalency_results": [],
            "accuracy": 0,  # Mark as failed
            "token_usage": _merge_usage(solve_usages) if solve_usages else None,
        }, 0, 0

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

            if equivalency_data.get("final_result") is True:
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
        "accuracy": accuracy,
        "token_usage": _merge_usage(solve_usages) if solve_usages else None,
    }, sympy_errors_correct_llm, sympy_errors

async def load_processed_ids(output_jsonl):
    """既存のresponse.jsonlから処理済みの問題IDを読み込む"""
    processed_ids = set()
    if os.path.exists(output_jsonl):
        try:
            async with aiofiles.open(output_jsonl, "r") as file:
                async for line in file:
                    if line.strip():
                        data = json.loads(line.strip())
                        entry_id = data.get("id")
                        if entry_id:
                            processed_ids.add(entry_id)
            print(f"既存の結果を検出: {len(processed_ids)}件の処理済み問題をスキップします")
        except Exception as e:
            print(f"既存の結果ファイルの読み込みエラー: {e}")
    return processed_ids

async def save_checkpoint(output_jsonl, results):
    """中間結果を保存（チェックポイント）"""
    try:
        async with aiofiles.open(output_jsonl, "a") as outfile:
            for result in results:
                await outfile.write(json.dumps(result, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"チェックポイント保存エラー: {e}")

async def process_jsonl(input_jsonl, output_dir, max_lines=1500, llm="gpt-5.2", batch_size=16):
    os.makedirs(output_dir, exist_ok=True)
    output_jsonl = os.path.join(output_dir, "response.jsonl")
    summary_csv = os.path.join(output_dir, "accuracy.csv")
    score_csv = os.path.join(output_dir, "score.csv")
    performance_plot = os.path.join(output_dir, "scatter_plot.png")

    # 既存の処理済みIDを読み込む（テスト用に無効化）
    # processed_ids = await load_processed_ids(output_jsonl)
    processed_ids = set()  # スキップしないように空セットに設定
    
    # 既存の結果を読み込む（再計算用）
    existing_results = []
    existing_accuracies = []
    
    if processed_ids:
        async with aiofiles.open(output_jsonl, "r") as file:
            async for line in file:
                if line.strip():
                    data = json.loads(line.strip())
                    existing_results.append(data)
                    existing_accuracies.append(data.get("accuracy", 0))
                    # 統計情報は再計算が必要なため、ここでは読み込まない

    # 新しい結果を保存するリスト
    new_results = []
    new_accuracies = []
    sympy_errors_correct_llm_total = 0
    sympy_errors_total = 0

    # エントリデータを読み込む（処理済みを除外）
    entries = []
    async with aiofiles.open(input_jsonl, "r") as file:
        async for line in file:
            if len(entries) >= max_lines:
                break
            data = json.loads(line.strip())
            entry_id = data.get("id")
            # 処理済みでないもののみ追加
            if entry_id not in processed_ids:
                entries.append(data)

    # 結果変数を初期化
    results = existing_results
    accuracies = existing_accuracies
    
    if not entries:
        print("処理する新しい問題がありません。すべて処理済みです。")
    else:
        print(f"新規処理対象: {len(entries)}問")
        
        # タスクを作成
        tasks = [process_entry(entry, llm) for entry in entries]

        # Split tasks into batches
        task_batches = [tasks[i:i + batch_size] for i in range(0, len(tasks), batch_size)]
        total_tasks = len(tasks)

        # 全体の進捗バー（問題単位）
        with tqdm_sync(total=total_tasks, desc=f"Processing {os.path.basename(input_jsonl)}", unit="問題", initial=len(processed_ids)) as pbar:
            # バッチ単位の進捗バー
            for batch in tqdm(task_batches, desc="Batches", unit="バッチ", leave=False):
                # レート制限回避のため、バッチ間に待機時間を追加
                if len(task_batches) > 1:
                    await asyncio.sleep(1)  # バッチ間に1秒待機
                batch_results = await asyncio.gather(*batch)
                
                batch_new_results = []
                for entry_result in batch_results:
                    if entry_result[0]:
                        batch_new_results.append(entry_result[0])
                        new_results.append(entry_result[0])
                        new_accuracies.append(entry_result[0]["accuracy"])
                        sympy_errors_correct_llm_total += entry_result[1]
                        sympy_errors_total += entry_result[2]
                    # 各問題の進捗を更新
                    pbar.update(1)
                
                # バッチ処理後にチェックポイントを保存
                if batch_new_results:
                    await save_checkpoint(output_jsonl, batch_new_results)
                
                # 現在の精度を表示（既存 + 新規）
                all_results_count = len(existing_results) + len(new_results)
                if existing_results or new_results:
                    all_accuracies = existing_accuracies + new_accuracies
                    current_accuracy = sum(all_accuracies) / len(all_accuracies) if all_accuracies else 0.0
                    pbar.set_postfix({
                        "精度": f"{current_accuracy:.2%}", 
                        "完了": f"{all_results_count}/{len(processed_ids) + total_tasks}",
                        "新規": f"{len(new_results)}"
                    })

        # 既存結果と新規結果を結合
        results = existing_results + new_results
        accuracies = existing_accuracies + new_accuracies

    overall_accuracy = sum(accuracies) / len(accuracies) if accuracies else 0.0
    variance = statistics.variance(accuracies) if len(accuracies) > 1 else 0.0
    sympy_error_ratio = sympy_errors_correct_llm_total / sympy_errors_total if sympy_errors_total > 0 else 0.0
    token_usages = [
        r.get("token_usage")
        for r in results
        if isinstance(r, dict) and isinstance(r.get("token_usage"), dict)
    ]
    total_token_usage = _merge_usage(token_usages) if token_usages else {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    avg_total_tokens = (total_token_usage["total_tokens"] / len(results)) if results else 0.0

    print(f"File: {os.path.basename(input_jsonl)} - Overall Accuracy: {overall_accuracy:.2f}, Variance: {variance:.4f}, Sympy Error Correct Ratio: {sympy_error_ratio:.4f}")
    print(
        "Token Usage - "
        f"Prompt: {total_token_usage['prompt_tokens']}, "
        f"Completion: {total_token_usage['completion_tokens']}, "
        f"Total: {total_token_usage['total_tokens']} "
        f"(Avg/Problem: {avg_total_tokens:.1f})"
    )
    print(f"処理済み: {len(existing_results)}問, 新規処理: {len(new_results)}問, 合計: {len(results)}問")

    # 最終結果を上書き保存（既存 + 新規を統合）
    async with aiofiles.open(output_jsonl, "w") as outfile:
        for result in results:
            await outfile.write(json.dumps(result, ensure_ascii=False) + "\n")

    with open(summary_csv, "w", newline="", encoding="utf-8") as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(
            [
                "Overall Accuracy",
                "Variance",
                "Sympy Error Correct Ratio",
                "Total Prompt Tokens",
                "Total Completion Tokens",
                "Total Tokens",
                "Avg Tokens / Problem",
            ]
        )
        csv_writer.writerow(
            [
                overall_accuracy,
                variance,
                sympy_error_ratio,
                total_token_usage["prompt_tokens"],
                total_token_usage["completion_tokens"],
                total_token_usage["total_tokens"],
                avg_total_tokens,
            ]
        )

    with open(score_csv, "w", newline="", encoding="utf-8") as scorefile:
        csv_writer = csv.writer(scorefile)
        csv_writer.writerow(["Entry ID", "Accuracy", "Prompt Tokens", "Completion Tokens", "Total Tokens"])
        for idx, accuracy in enumerate(accuracies):
            usage = results[idx].get("token_usage") if isinstance(results[idx], dict) else None
            if not isinstance(usage, dict):
                usage = {"prompt_tokens": "", "completion_tokens": "", "total_tokens": ""}
            csv_writer.writerow(
                [
                    results[idx]["id"],
                    accuracy,
                    usage.get("prompt_tokens", ""),
                    usage.get("completion_tokens", ""),
                    usage.get("total_tokens", ""),
                ]
            )

    plt.figure()
    plt.scatter(range(len(accuracies)), accuracies, label="Accuracy Scores")
    plt.axhline(overall_accuracy, color="green", linestyle="--", label=f"Mean: {overall_accuracy:.2f}")
    plt.axhline(statistics.median(accuracies), color="blue", linestyle="--", label=f"Median: {statistics.median(accuracies):.2f}")
    if len(accuracies) > 1:
        plt.axhline(overall_accuracy + statistics.stdev(accuracies), color="red", linestyle="--", label=f"+1 Std Dev: {overall_accuracy + statistics.stdev(accuracies):.2f}")
        plt.axhline(overall_accuracy - statistics.stdev(accuracies), color="red", linestyle="--", label=f"-1 Std Dev: {overall_accuracy - statistics.stdev(accuracies):.2f}")
    plt.title(f"{llm} Performance Plot for {os.path.basename(input_jsonl)} (No Reasoning)")
    plt.xlabel("Entry Index")
    plt.ylabel("Correctness")
    plt.legend()
    plt.savefig(performance_plot)

    print(f"Results saved to {output_dir}. JSONL: {output_jsonl}, Summary: {summary_csv}, Scores: {score_csv}, Plot: {performance_plot}.")


async def process_jsonl_list(jsonl_list, base_output_dir, max_lines=1500, llm="gpt-5.2", batch_size=32):
    for input_jsonl in jsonl_list:
        jsonl_name = os.path.splitext(os.path.basename(input_jsonl))[0]
        output_dir = os.path.join(base_output_dir, jsonl_name)
        print(f"Starting processing for {input_jsonl}...")
        await process_jsonl(input_jsonl, output_dir, max_lines, llm, batch_size)

def main(llm, base_output_dir, input_jsonl_list, max_lines=1500, batch_size=32):
    asyncio.run(process_jsonl_list(input_jsonl_list, base_output_dir, max_lines, llm, batch_size))

if __name__ == "__main__":
    # ==========================================
    # 力学データセット専用設定（GPT-5.2、reasoningパラメータなし版）
    # ==========================================
    llm = "gpt-5.2"
    base_output_dir = "../outputs/gpt-5.2_mechanics_output_no_reasoning_textonly"
    
    # テキストのみ版を使用
    mechanics_dataset = "../PHYSICS/PHYSICS-textonly/mechanics_dataset_textonly.jsonl"
    
    # 画像付き版を使用する場合は以下をコメントアウトして有効化
    # mechanics_dataset = "../PHYSICS/mechanics_dataset.jsonl"
    
    input_jsonl_list = [mechanics_dataset]
    
    # 評価する問題数（textonly版は133問）
    max_lines = 133  # 全問題を評価（textonly版は133問）
    
    # バッチサイズを24に設定
    batch_size = 24
    
    print("=" * 60)
    print("力学データセット評価開始（GPT-5.2、reasoningパラメータなし）")
    print(f"モデル: {llm}")
    print(f"データセット: {mechanics_dataset}")
    print(f"最大問題数: {max_lines}")
    print(f"バッチサイズ: {batch_size}")
    print(f"出力先: {base_output_dir}")
    print("=" * 60)
    
    main(llm, base_output_dir, input_jsonl_list, max_lines, batch_size)
