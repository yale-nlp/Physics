"""
reasoningパラメータ有無による結果比較スクリプト

このスクリプトは、reasoningパラメータを追加する前後の評価結果を比較します。
"""

import os
import json
import csv
import statistics
from typing import Any
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def load_jsonl_results(jsonl_path: str) -> list[dict[str, Any]]:
    """JSONLファイルから結果を読み込む"""
    results = []
    if os.path.exists(jsonl_path):
        with open(jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    results.append(json.loads(line.strip()))
    return results

def load_csv_summary(csv_path: str) -> dict[str, Any]:
    """CSVサマリーファイルから統計情報を読み込む"""
    summary = {}
    if os.path.exists(csv_path):
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                summary = row
                break
    return summary

def compare_results(
    without_reasoning_dir: str,
    with_reasoning_dir: str,
    output_dir: str
):
    """2つの評価結果を比較"""
    os.makedirs(output_dir, exist_ok=True)
    
    # ファイルパス
    without_reasoning_jsonl = os.path.join(without_reasoning_dir, "response.jsonl")
    without_reasoning_csv = os.path.join(without_reasoning_dir, "accuracy.csv")
    
    with_reasoning_jsonl = os.path.join(with_reasoning_dir, "response.jsonl")
    with_reasoning_csv = os.path.join(with_reasoning_dir, "accuracy.csv")
    
    # 結果を読み込む
    print(f"reasoningなしの結果を読み込み中: {without_reasoning_jsonl}")
    results_without = load_jsonl_results(without_reasoning_jsonl)
    summary_without = load_csv_summary(without_reasoning_csv)
    
    print(f"reasoningありの結果を読み込み中: {with_reasoning_jsonl}")
    results_with = load_jsonl_results(with_reasoning_jsonl)
    summary_with = load_csv_summary(with_reasoning_csv)
    
    # IDでインデックス化
    results_without_dict = {r["id"]: r for r in results_without}
    results_with_dict = {r["id"]: r for r in results_with}
    
    # 共通の問題IDを取得
    common_ids = set(results_without_dict.keys()) & set(results_with_dict.keys())
    print(f"\n共通の問題数: {len(common_ids)}")
    print(f"reasoningなしの問題数: {len(results_without_dict)}")
    print(f"reasoningありの問題数: {len(results_with_dict)}")
    
    # 比較データを収集
    comparison_data = []
    accuracy_without_list = []
    accuracy_with_list = []
    accuracy_diff_list = []
    
    token_usage_without = {"prompt": 0, "completion": 0, "total": 0}
    token_usage_with = {"prompt": 0, "completion": 0, "total": 0}
    
    for entry_id in sorted(common_ids):
        result_without = results_without_dict[entry_id]
        result_with = results_with_dict[entry_id]
        
        accuracy_without = result_without.get("accuracy", 0)
        accuracy_with = result_with.get("accuracy", 0)
        accuracy_diff = accuracy_with - accuracy_without
        
        accuracy_without_list.append(accuracy_without)
        accuracy_with_list.append(accuracy_with)
        accuracy_diff_list.append(accuracy_diff)
        
        # トークン使用量
        usage_without = result_without.get("token_usage") or {}
        usage_with = result_with.get("token_usage") or {}
        
        if isinstance(usage_without, dict):
            token_usage_without["prompt"] += usage_without.get("prompt_tokens", 0)
            token_usage_without["completion"] += usage_without.get("completion_tokens", 0)
            token_usage_without["total"] += usage_without.get("total_tokens", 0)
        
        if isinstance(usage_with, dict):
            token_usage_with["prompt"] += usage_with.get("prompt_tokens", 0)
            token_usage_with["completion"] += usage_with.get("completion_tokens", 0)
            token_usage_with["total"] += usage_with.get("total_tokens", 0)
        
        comparison_data.append({
            "id": entry_id,
            "accuracy_without_reasoning": accuracy_without,
            "accuracy_with_reasoning": accuracy_with,
            "accuracy_diff": accuracy_diff,
            "improved": accuracy_diff > 0,
            "degraded": accuracy_diff < 0,
            "same": accuracy_diff == 0,
            "prompt_tokens_without": usage_without.get("prompt_tokens", ""),
            "completion_tokens_without": usage_without.get("completion_tokens", ""),
            "total_tokens_without": usage_without.get("total_tokens", ""),
            "prompt_tokens_with": usage_with.get("prompt_tokens", ""),
            "completion_tokens_with": usage_with.get("completion_tokens", ""),
            "total_tokens_with": usage_with.get("total_tokens", ""),
        })
    
    # 統計を計算
    avg_accuracy_without = statistics.mean(accuracy_without_list) if accuracy_without_list else 0
    avg_accuracy_with = statistics.mean(accuracy_with_list) if accuracy_with_list else 0
    avg_accuracy_diff = statistics.mean(accuracy_diff_list) if accuracy_diff_list else 0
    
    improved_count = sum(1 for d in comparison_data if d["improved"])
    degraded_count = sum(1 for d in comparison_data if d["degraded"])
    same_count = sum(1 for d in comparison_data if d["same"])
    
    # CSVに保存
    comparison_csv = os.path.join(output_dir, "comparison.csv")
    with open(comparison_csv, "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "id", "accuracy_without_reasoning", "accuracy_with_reasoning", "accuracy_diff",
            "improved", "degraded", "same",
            "prompt_tokens_without", "completion_tokens_without", "total_tokens_without",
            "prompt_tokens_with", "completion_tokens_with", "total_tokens_with"
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(comparison_data)
    
    # サマリーCSV
    summary_csv = os.path.join(output_dir, "summary.csv")
    with open(summary_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Metric", "Without Reasoning", "With Reasoning", "Difference"])
        writer.writerow(["Average Accuracy", f"{avg_accuracy_without:.4f}", f"{avg_accuracy_with:.4f}", f"{avg_accuracy_diff:.4f}"])
        writer.writerow(["Improved Problems", "", "", str(improved_count)])
        writer.writerow(["Degraded Problems", "", "", str(degraded_count)])
        writer.writerow(["Same Results", "", "", str(same_count)])
        writer.writerow(["Total Prompt Tokens", token_usage_without["prompt"], token_usage_with["prompt"], token_usage_with["prompt"] - token_usage_without["prompt"]])
        writer.writerow(["Total Completion Tokens", token_usage_without["completion"], token_usage_with["completion"], token_usage_with["completion"] - token_usage_without["completion"]])
        writer.writerow(["Total Tokens", token_usage_without["total"], token_usage_with["total"], token_usage_with["total"] - token_usage_without["total"]])
        if len(common_ids) > 0:
            writer.writerow(["Avg Tokens per Problem", 
                           f"{token_usage_without['total'] / len(common_ids):.1f}", 
                           f"{token_usage_with['total'] / len(common_ids):.1f}",
                           f"{(token_usage_with['total'] - token_usage_without['total']) / len(common_ids):.1f}"])
    
    # プロットを作成
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    
    # 1. Accuracy比較（散布図）
    ax1 = axes[0, 0]
    ax1.scatter(accuracy_without_list, accuracy_with_list, alpha=0.6)
    ax1.plot([0, 1], [0, 1], 'r--', label='y=x')
    ax1.set_xlabel("Accuracy (Without Reasoning)")
    ax1.set_ylabel("Accuracy (With Reasoning)")
    ax1.set_title("Accuracy Comparison")
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 2. Accuracy差分の分布
    ax2 = axes[0, 1]
    ax2.hist(accuracy_diff_list, bins=20, edgecolor='black', alpha=0.7)
    ax2.axvline(0, color='r', linestyle='--', label='No Change')
    ax2.set_xlabel("Accuracy Difference (With - Without)")
    ax2.set_ylabel("Frequency")
    ax2.set_title("Accuracy Difference Distribution")
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 3. トークン使用量比較
    ax3 = axes[1, 0]
    categories = ["Prompt", "Completion", "Total"]
    without_values = [token_usage_without["prompt"], token_usage_without["completion"], token_usage_without["total"]]
    with_values = [token_usage_with["prompt"], token_usage_with["completion"], token_usage_with["total"]]
    x = range(len(categories))
    width = 0.35
    ax3.bar([i - width/2 for i in x], without_values, width, label="Without Reasoning", alpha=0.8)
    ax3.bar([i + width/2 for i in x], with_values, width, label="With Reasoning", alpha=0.8)
    ax3.set_ylabel("Tokens")
    ax3.set_title("Token Usage Comparison")
    ax3.set_xticks(x)
    ax3.set_xticklabels(categories)
    ax3.legend()
    ax3.grid(True, alpha=0.3, axis='y')
    
    # 4. 改善/悪化の内訳
    ax4 = axes[1, 1]
    labels = ["Improved", "Degraded", "Same"]
    sizes = [improved_count, degraded_count, same_count]
    colors = ['green', 'red', 'gray']
    ax4.pie(sizes, labels=labels, autopct='%1.1f%%', colors=colors, startangle=90)
    ax4.set_title("Result Changes Distribution")
    
    plt.tight_layout()
    plot_path = os.path.join(output_dir, "comparison_plots.png")
    plt.savefig(plot_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    # レポートを生成
    report_path = os.path.join(output_dir, "comparison_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Reasoningパラメータ有無による結果比較\n\n")
        f.write(f"## 概要\n\n")
        f.write(f"- 比較対象問題数: {len(common_ids)}\n")
        f.write(f"- reasoningなしの問題数: {len(results_without_dict)}\n")
        f.write(f"- reasoningありの問題数: {len(results_with_dict)}\n\n")
        
        f.write(f"## 精度比較\n\n")
        f.write(f"- **平均精度（reasoningなし）**: {avg_accuracy_without:.4f} ({avg_accuracy_without*100:.2f}%)\n")
        f.write(f"- **平均精度（reasoningあり）**: {avg_accuracy_with:.4f} ({avg_accuracy_with*100:.2f}%)\n")
        f.write(f"- **平均精度差**: {avg_accuracy_diff:.4f} ({avg_accuracy_diff*100:.2f}%)\n\n")
        
        f.write(f"## 結果の変化\n\n")
        f.write(f"- **改善した問題**: {improved_count}問 ({improved_count/len(common_ids)*100:.1f}%)\n")
        f.write(f"- **悪化した問題**: {degraded_count}問 ({degraded_count/len(common_ids)*100:.1f}%)\n")
        f.write(f"- **変化なし**: {same_count}問 ({same_count/len(common_ids)*100:.1f}%)\n\n")
        
        f.write(f"## トークン使用量比較\n\n")
        f.write(f"### reasoningなし\n")
        f.write(f"- Prompt Tokens: {token_usage_without['prompt']:,}\n")
        f.write(f"- Completion Tokens: {token_usage_without['completion']:,}\n")
        f.write(f"- Total Tokens: {token_usage_without['total']:,}\n")
        if len(common_ids) > 0:
            f.write(f"- Avg Tokens per Problem: {token_usage_without['total'] / len(common_ids):.1f}\n\n")
        
        f.write(f"### reasoningあり\n")
        f.write(f"- Prompt Tokens: {token_usage_with['prompt']:,}\n")
        f.write(f"- Completion Tokens: {token_usage_with['completion']:,}\n")
        f.write(f"- Total Tokens: {token_usage_with['total']:,}\n")
        if len(common_ids) > 0:
            f.write(f"- Avg Tokens per Problem: {token_usage_with['total'] / len(common_ids):.1f}\n\n")
        
        f.write(f"### 差分\n")
        f.write(f"- Prompt Tokens: {token_usage_with['prompt'] - token_usage_without['prompt']:,}\n")
        f.write(f"- Completion Tokens: {token_usage_with['completion'] - token_usage_without['completion']:,}\n")
        f.write(f"- Total Tokens: {token_usage_with['total'] - token_usage_without['total']:,}\n")
        if len(common_ids) > 0:
            diff_avg = (token_usage_with['total'] - token_usage_without['total']) / len(common_ids)
            f.write(f"- Avg Tokens per Problem: {diff_avg:.1f}\n\n")
        
        f.write(f"## ファイル\n\n")
        f.write(f"- 詳細比較CSV: `comparison.csv`\n")
        f.write(f"- サマリーCSV: `summary.csv`\n")
        f.write(f"- 比較プロット: `comparison_plots.png`\n")
    
    print(f"\n比較結果を保存しました:")
    print(f"  - {comparison_csv}")
    print(f"  - {summary_csv}")
    print(f"  - {plot_path}")
    print(f"  - {report_path}")
    
    print(f"\n=== 比較サマリー ===")
    print(f"平均精度（reasoningなし）: {avg_accuracy_without:.4f} ({avg_accuracy_without*100:.2f}%)")
    print(f"平均精度（reasoningあり）: {avg_accuracy_with:.4f} ({avg_accuracy_with*100:.2f}%)")
    print(f"平均精度差: {avg_accuracy_diff:.4f} ({avg_accuracy_diff*100:.2f}%)")
    print(f"改善: {improved_count}問, 悪化: {degraded_count}問, 変化なし: {same_count}問")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 4:
        print("使用方法: python compare_reasoning_results.py <reasoningなしディレクトリ> <reasoningありディレクトリ> <出力ディレクトリ>")
        print("\n例:")
        print("  python compare_reasoning_results.py \\")
        print("    ../outputs/gpt-5.2_mechanics_output_no_reasoning/mechanics_dataset \\")
        print("    ../outputs/gpt-5.2_mechanics_output/mechanics_dataset \\")
        print("    ../outputs/reasoning_comparison")
        sys.exit(1)
    
    without_reasoning_dir = sys.argv[1]
    with_reasoning_dir = sys.argv[2]
    output_dir = sys.argv[3]
    
    compare_results(without_reasoning_dir, with_reasoning_dir, output_dir)
