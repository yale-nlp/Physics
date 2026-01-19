"""
重複を除去して評価結果を再計算するスクリプト

response.jsonlから重複している問題IDを除去し、
各問題IDについて最新の結果のみを保持して統計を再計算します。
"""

import os
import sys
import json
import csv
import statistics
import matplotlib
from pathlib import Path
from collections import OrderedDict

matplotlib.use("Agg")
import matplotlib.pyplot as plt

def remove_duplicates_and_recalculate(input_jsonl_path, output_dir):
    """
    重複を除去して評価結果を再計算
    
    Args:
        input_jsonl_path: 入力となるresponse.jsonlのパス
        output_dir: 出力ディレクトリ
    """
    # 結果を読み込む（重複を除去：各IDについて最新の結果のみを保持）
    results_by_id = OrderedDict()
    
    print(f"Reading {input_jsonl_path}...")
    with open(input_jsonl_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                data = json.loads(line.strip())
                entry_id = data.get("id")
                if entry_id:
                    # 同じIDが既に存在する場合は上書き（最新の結果を保持）
                    if entry_id in results_by_id:
                        print(f"  Warning: Duplicate ID found: {entry_id} (line {line_num})")
                    results_by_id[entry_id] = data
            except json.JSONDecodeError as e:
                print(f"  Error parsing line {line_num}: {e}")
                continue
    
    # 重複除去後の結果リスト
    results = list(results_by_id.values())
    
    print(f"\nOriginal entries: {line_num}")
    print(f"Unique entries: {len(results)}")
    print(f"Duplicates removed: {line_num - len(results)}")
    
    # 統計を計算
    accuracies = [r.get("accuracy", 0) for r in results if isinstance(r.get("accuracy"), (int, float))]
    
    if not accuracies:
        print("No accuracy data found!")
        return
    
    overall_accuracy = sum(accuracies) / len(accuracies) if accuracies else 0.0
    variance = statistics.variance(accuracies) if len(accuracies) > 1 else 0.0
    
    # Sympy Error Correct Ratioを計算
    sympy_errors_correct_llm_total = 0
    sympy_errors_total = 0
    
    for r in results:
        equivalency_results = r.get("equivalency_results", [])
        if not isinstance(equivalency_results, list):
            continue
        
        for eq_result in equivalency_results:
            if not isinstance(eq_result, dict):
                continue
            
            sympy_result = eq_result.get("sympy_result")
            llm_result = eq_result.get("llm_result")
            
            if sympy_result is False and llm_result is True:
                sympy_errors_correct_llm_total += 1
            if sympy_result is not None:
                sympy_errors_total += 1
    
    sympy_error_ratio = sympy_errors_correct_llm_total / sympy_errors_total if sympy_errors_total > 0 else 0.0
    
    # トークン使用量を計算
    token_usages = [
        r.get("token_usage")
        for r in results
        if isinstance(r, dict) and isinstance(r.get("token_usage"), dict)
    ]
    
    total_token_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    for usage in token_usages:
        for k in total_token_usage:
            v = usage.get(k)
            if isinstance(v, int):
                total_token_usage[k] += v
    
    avg_total_tokens = (total_token_usage["total_tokens"] / len(results)) if results else 0.0
    
    # 結果を表示
    print(f"\n=== Recalculated Statistics ===")
    print(f"Overall Accuracy: {overall_accuracy:.4f} ({overall_accuracy*100:.2f}%)")
    print(f"Variance: {variance:.4f}")
    print(f"Sympy Error Correct Ratio: {sympy_error_ratio:.4f}")
    print(f"Total Tokens: {total_token_usage['total_tokens']}")
    print(f"Avg Tokens / Problem: {avg_total_tokens:.1f}")
    
    # 出力ディレクトリを作成
    os.makedirs(output_dir, exist_ok=True)
    
    # response.jsonlを保存（重複除去後）
    output_jsonl = os.path.join(output_dir, "response.jsonl")
    with open(output_jsonl, 'w', encoding='utf-8') as f:
        for result in results:
            f.write(json.dumps(result, ensure_ascii=False) + '\n')
    print(f"\nSaved deduplicated results to: {output_jsonl}")
    
    # accuracy.csvを保存
    summary_csv = os.path.join(output_dir, "accuracy.csv")
    with open(summary_csv, 'w', newline='', encoding='utf-8') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow([
            "Overall Accuracy",
            "Variance",
            "Sympy Error Correct Ratio",
            "Total Prompt Tokens",
            "Total Completion Tokens",
            "Total Tokens",
            "Avg Tokens / Problem",
        ])
        csv_writer.writerow([
            overall_accuracy,
            variance,
            sympy_error_ratio,
            total_token_usage["prompt_tokens"],
            total_token_usage["completion_tokens"],
            total_token_usage["total_tokens"],
            avg_total_tokens,
        ])
    print(f"Saved accuracy summary to: {summary_csv}")
    
    # score.csvを保存
    score_csv = os.path.join(output_dir, "score.csv")
    with open(score_csv, 'w', newline='', encoding='utf-8') as scorefile:
        csv_writer = csv.writer(scorefile)
        csv_writer.writerow(["Entry ID", "Accuracy", "Prompt Tokens", "Completion Tokens", "Total Tokens"])
        for r in results:
            accuracy = r.get("accuracy", 0)
            usage = r.get("token_usage") if isinstance(r.get("token_usage"), dict) else None
            if not isinstance(usage, dict):
                usage = {"prompt_tokens": "", "completion_tokens": "", "total_tokens": ""}
            csv_writer.writerow([
                r["id"],
                accuracy,
                usage.get("prompt_tokens", ""),
                usage.get("completion_tokens", ""),
                usage.get("total_tokens", ""),
            ])
    print(f"Saved score details to: {score_csv}")
    
    # scatter_plot.pngを生成
    performance_plot = os.path.join(output_dir, "scatter_plot.png")
    plt.figure()
    plt.scatter(range(len(accuracies)), accuracies, label="Accuracy Scores")
    plt.axhline(overall_accuracy, color="green", linestyle="--", label=f"Mean: {overall_accuracy:.2f}")
    plt.axhline(statistics.median(accuracies), color="blue", linestyle="--", label=f"Median: {statistics.median(accuracies):.2f}")
    if len(accuracies) > 1:
        std_dev = statistics.stdev(accuracies)
        plt.axhline(overall_accuracy + std_dev, color="red", linestyle="--", label=f"+1 Std Dev: {overall_accuracy + std_dev:.2f}")
        plt.axhline(overall_accuracy - std_dev, color="red", linestyle="--", label=f"-1 Std Dev: {overall_accuracy - std_dev:.2f}")
    plt.title(f"GPT-4o Performance Plot (Deduplicated)")
    plt.xlabel("Entry Index")
    plt.ylabel("Correctness")
    plt.legend()
    plt.savefig(performance_plot)
    print(f"Saved performance plot to: {performance_plot}")
    
    print(f"\n=== Deduplication Complete ===")
    print(f"Results saved to: {output_dir}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Remove duplicates and recalculate evaluation results")
    parser.add_argument(
        "input_jsonl",
        type=str,
        help="Input response.jsonl file path"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory (default: same as input file directory)"
    )
    
    args = parser.parse_args()
    
    input_path = Path(args.input_jsonl)
    if not input_path.exists():
        print(f"Error: File not found: {input_path}")
        sys.exit(1)
    
    if args.output_dir:
        output_dir = args.output_dir
    else:
        # デフォルトは入力ファイルと同じディレクトリ
        output_dir = str(input_path.parent)
    
    remove_duplicates_and_recalculate(str(input_path), output_dir)
