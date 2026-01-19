#!/usr/bin/env python3
"""
途中式でboxed形式が使われているかを分析するスクリプト
特にGPT-5.2で途中式に\boxed{}が使われ、精度が下がっている可能性を調査
"""

import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Dict, List, Any
import re
from collections import Counter

# 日本語フォント設定
plt.rcParams['font.family'] = 'DejaVu Sans'
sns.set_style("whitegrid")
sns.set_palette("husl")

def load_responses(file_path: Path) -> List[Dict[str, Any]]:
    """response.jsonlを読み込む"""
    responses = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                responses.append(json.loads(line))
    return responses

def count_boxed_in_solution(solution: str) -> int:
    """solution内の\boxed{}の数をカウント"""
    if not solution:
        return 0
    # 様々なboxed形式をカウント
    patterns = [
        r'\\boxed\{',
        r'\\\[boxed\{',
        r'\\\\\[boxed\{',
    ]
    count = 0
    for pattern in patterns:
        matches = re.findall(pattern, solution, re.IGNORECASE)
        count += len(matches)
    return count

def analyze_intermediate_boxed(responses: List[Dict], model_name: str) -> Dict:
    """途中式でのboxed使用を分析"""
    total = len(responses)
    
    # final_answersの数の分布
    final_answer_counts = []
    
    # boxed数の分布
    boxed_counts = []
    
    # 精度とfinal_answers数の関係
    accuracy_vs_count = []
    
    # 精度とboxed数の関係
    accuracy_vs_boxed = []
    
    # ケース分析
    high_count_cases = []  # final_answersが3個以上のケース
    intermediate_boxed_cases = []  # boxedが2個以上のケース
    
    for resp in responses:
        final_answers = resp.get('final_answers', [])
        solution = resp.get('solution', '')
        accuracy = resp.get('accuracy', 0)
        
        final_answer_count = len(final_answers) if final_answers else 0
        final_answer_counts.append(final_answer_count)
        
        boxed_count = count_boxed_in_solution(solution) if solution else 0
        boxed_counts.append(boxed_count)
        
        accuracy_vs_count.append({
            'final_answer_count': final_answer_count,
            'accuracy': accuracy
        })
        
        accuracy_vs_boxed.append({
            'boxed_count': boxed_count,
            'accuracy': accuracy
        })
        
        # 高カウントケースを記録
        if final_answer_count >= 3:
            high_count_cases.append({
                'id': resp.get('id', 'unknown'),
                'final_answer_count': final_answer_count,
                'boxed_count': boxed_count,
                'accuracy': accuracy,
                'solution_preview': solution[:300] + '...' if solution and len(solution) > 300 else solution
            })
        
        # 途中式でboxedを使っている可能性があるケース
        if boxed_count >= 2 and final_answer_count >= 2:
            intermediate_boxed_cases.append({
                'id': resp.get('id', 'unknown'),
                'final_answer_count': final_answer_count,
                'boxed_count': boxed_count,
                'accuracy': accuracy,
                'solution_preview': solution[:300] + '...' if solution and len(solution) > 300 else solution
            })
    
    return {
        'model_name': model_name,
        'total_entries': total,
        'final_answer_counts': final_answer_counts,
        'boxed_counts': boxed_counts,
        'accuracy_vs_count': accuracy_vs_count,
        'accuracy_vs_boxed': accuracy_vs_boxed,
        'high_count_cases': high_count_cases,
        'intermediate_boxed_cases': intermediate_boxed_cases,
        'avg_final_answers': sum(final_answer_counts) / len(final_answer_counts) if final_answer_counts else 0,
        'avg_boxed_count': sum(boxed_counts) / len(boxed_counts) if boxed_counts else 0,
        'max_final_answers': max(final_answer_counts) if final_answer_counts else 0,
        'max_boxed_count': max(boxed_counts) if boxed_counts else 0,
    }

def visualize_intermediate_boxed(all_stats: Dict[str, Dict], output_dir: Path):
    """途中式boxedの可視化"""
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    
    model_names = list(all_stats.keys())
    colors = sns.color_palette("husl", len(model_names))
    
    # 1. final_answers数の分布
    for i, name in enumerate(model_names):
        counts = all_stats[name]['final_answer_counts']
        axes[0, 0].hist(counts, bins=range(0, max(max(counts), 10) + 2), 
                       alpha=0.6, label=name, edgecolor='black', align='left')
    axes[0, 0].set_xlabel('Number of Final Answers')
    axes[0, 0].set_ylabel('Frequency')
    axes[0, 0].set_title('Final Answers Count Distribution')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)
    
    # 2. boxed数の分布
    for i, name in enumerate(model_names):
        counts = all_stats[name]['boxed_counts']
        max_boxed = max(max(counts), 5) if counts else 5
        axes[0, 1].hist(counts, bins=range(0, max_boxed + 2), 
                       alpha=0.6, label=name, edgecolor='black', align='left')
    axes[0, 1].set_xlabel('Number of \\boxed{} in Solution')
    axes[0, 1].set_ylabel('Frequency')
    axes[0, 1].set_title('Boxed Count Distribution')
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)
    
    # 3. final_answers数と精度の関係
    for i, name in enumerate(model_names):
        data = all_stats[name]['accuracy_vs_count']
        df = pd.DataFrame(data)
        if len(df) > 0:
            grouped = df.groupby('final_answer_count')['accuracy'].mean()
            axes[0, 2].plot(grouped.index, grouped.values, marker='o', label=name, linewidth=2)
    axes[0, 2].set_xlabel('Number of Final Answers')
    axes[0, 2].set_ylabel('Mean Accuracy')
    axes[0, 2].set_title('Accuracy vs Final Answers Count')
    axes[0, 2].legend()
    axes[0, 2].grid(True, alpha=0.3)
    
    # 4. boxed数と精度の関係
    for i, name in enumerate(model_names):
        data = all_stats[name]['accuracy_vs_boxed']
        df = pd.DataFrame(data)
        if len(df) > 0:
            grouped = df.groupby('boxed_count')['accuracy'].mean()
            axes[1, 0].plot(grouped.index, grouped.values, marker='o', label=name, linewidth=2)
    axes[1, 0].set_xlabel('Number of \\boxed{} in Solution')
    axes[1, 0].set_ylabel('Mean Accuracy')
    axes[1, 0].set_title('Accuracy vs Boxed Count')
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)
    
    # 5. 統計サマリー
    stats_text = "Statistics Summary:\n\n"
    for name in model_names:
        stats = all_stats[name]
        stats_text += f"{name}:\n"
        stats_text += f"  Avg Final Answers: {stats['avg_final_answers']:.2f}\n"
        stats_text += f"  Max Final Answers: {stats['max_final_answers']}\n"
        stats_text += f"  Avg Boxed Count: {stats['avg_boxed_count']:.2f}\n"
        stats_text += f"  Max Boxed Count: {stats['max_boxed_count']}\n"
        stats_text += f"  High Count Cases (≥3): {len(stats['high_count_cases'])}\n"
        stats_text += f"  Intermediate Boxed Cases: {len(stats['intermediate_boxed_cases'])}\n\n"
    
    axes[1, 1].text(0.1, 0.5, stats_text, fontsize=9, verticalalignment='center',
                    family='monospace', transform=axes[1, 1].transAxes)
    axes[1, 1].axis('off')
    axes[1, 1].set_title('Statistics Summary')
    
    # 6. final_answers数が3個以上のケースの割合
    high_count_rates = []
    for name in model_names:
        stats = all_stats[name]
        high_count_rate = len(stats['high_count_cases']) / stats['total_entries'] if stats['total_entries'] > 0 else 0
        high_count_rates.append(high_count_rate)
    
    axes[1, 2].bar(range(len(model_names)), high_count_rates, color=colors, alpha=0.7)
    axes[1, 2].set_xticks(range(len(model_names)))
    axes[1, 2].set_xticklabels(model_names, rotation=45, ha='right')
    axes[1, 2].set_ylabel('Rate of Cases with ≥3 Final Answers')
    axes[1, 2].set_title('High Final Answers Count Rate')
    axes[1, 2].grid(True, alpha=0.3, axis='y')
    for i, rate in enumerate(high_count_rates):
        axes[1, 2].text(i, rate + 0.01, f'{rate:.3f}', ha='center', va='bottom')
    
    plt.tight_layout()
    plt.savefig(output_dir / 'intermediate_boxed_analysis.png', dpi=300, bbox_inches='tight')
    print(f"Saved: {output_dir / 'intermediate_boxed_analysis.png'}")
    plt.close()

def generate_intermediate_boxed_report(all_stats: Dict[str, Dict], output_dir: Path):
    """途中式boxedのレポートを生成"""
    report = f"""
# 途中式でのBoxed形式使用分析レポート

## 1. 統計サマリー

"""
    
    for name in all_stats.keys():
        stats = all_stats[name]
        report += f"""
### {name}
- 平均Final Answers数: {stats['avg_final_answers']:.2f}
- 最大Final Answers数: {stats['max_final_answers']}
- 平均Boxed数: {stats['avg_boxed_count']:.2f}
- 最大Boxed数: {stats['max_boxed_count']}
- Final Answers数が3個以上のケース: {len(stats['high_count_cases'])}件 ({len(stats['high_count_cases'])/stats['total_entries']*100:.2f}%)
- 途中式でboxedを使用している可能性があるケース: {len(stats['intermediate_boxed_cases'])}件
"""
    
    report += "\n## 2. 主な発見\n\n"
    
    # final_answers数の比較
    avg_counts = {name: all_stats[name]['avg_final_answers'] for name in all_stats.keys()}
    sorted_models = sorted(avg_counts.items(), key=lambda x: x[1], reverse=True)
    
    report += "### Final Answers数の比較\n"
    report += "1. **平均Final Answers数ランキング**:\n"
    for rank, (name, count) in enumerate(sorted_models, 1):
        report += f"   {rank}. {name}: {count:.2f}\n"
    
    # 精度への影響
    report += "\n### 精度への影響\n"
    report += "**採点指標**: `accuracy = 正解数 / 抽出解数`\n\n"
    report += "途中式で`\\boxed{}`を使うと、抽出される回答数が増え、精度が下がる可能性があります。\n\n"
    
    # 高カウントケースの分析
    report += "## 3. Final Answers数が3個以上のケース（サンプル）\n\n"
    for name in all_stats.keys():
        cases = all_stats[name]['high_count_cases']
        if cases:
            report += f"### {name} ({len(cases)}件)\n\n"
            for i, case in enumerate(cases[:5], 1):  # 上位5件
                report += f"{i}. Entry ID: {case['id']}\n"
                report += f"   - Final Answers数: {case['final_answer_count']}\n"
                report += f"   - Boxed数: {case['boxed_count']}\n"
                report += f"   - Accuracy: {case['accuracy']:.4f}\n"
                if case['solution_preview']:
                    report += f"   - Solution preview: {case['solution_preview'][:150]}...\n"
                report += "\n"
    
    # 途中式boxedケースの分析
    report += "## 4. 途中式でBoxedを使用している可能性があるケース\n\n"
    for name in all_stats.keys():
        cases = all_stats[name]['intermediate_boxed_cases']
        if cases:
            report += f"### {name} ({len(cases)}件)\n\n"
            for i, case in enumerate(cases[:5], 1):  # 上位5件
                report += f"{i}. Entry ID: {case['id']}\n"
                report += f"   - Final Answers数: {case['final_answer_count']}\n"
                report += f"   - Boxed数: {case['boxed_count']}\n"
                report += f"   - Accuracy: {case['accuracy']:.4f}\n"
                if case['solution_preview']:
                    report += f"   - Solution preview: {case['solution_preview'][:150]}...\n"
                report += "\n"
    
    report += "\n## 5. 結論\n\n"
    report += "GPT-5.2のように途中式でも`\\boxed{}`を使うと、抽出される回答数が増え、\n"
    report += "採点指標（accuracy = 正解数 / 抽出解数）により精度が下がる可能性があります。\n"
    report += "一方、o3-miniのようにfinal_answers=1固定の場合は、このペナルティを受けません。\n"
    
    with open(output_dir / 'intermediate_boxed_report.md', 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"Saved: {output_dir / 'intermediate_boxed_report.md'}")
    print("\n" + "="*80)
    print(report)
    print("="*80)

def main():
    base_dir = Path("/Users/takahashiryoutarou/Desktop/LLM実験/Physics/outputs")
    
    # 最近追加されたoutputの定義
    output_configs = [
        ("gemini-3.0-pro", "gemini-3.0-pro_output/mechanics_dataset/response.jsonl"),
        ("gpt-5.2", "gpt-5.2_mechanics_output/mechanics_dataset/response.jsonl"),
        ("gpt-4o-rerun", "gpt-4o_mechanics_output_rerun/mechanics_dataset/response.jsonl"),
    ]
    
    # o3-miniも追加
    o3_path = base_dir / "o3-mini_together_output/mechanics_dataset_textonly/response.jsonl"
    if o3_path.exists():
        output_configs.append(("o3-mini", "o3-mini_together_output/mechanics_dataset_textonly/response.jsonl"))
    
    print("データを読み込んでいます...")
    all_responses = {}
    for name, file_path in output_configs:
        try:
            responses = load_responses(base_dir / file_path)
            all_responses[name] = responses
            print(f"✓ {name}: {len(responses)}件のエントリを読み込み")
        except Exception as e:
            print(f"✗ {name}: 読み込みエラー - {e}")
            continue
    
    if not all_responses:
        print("エラー: データを読み込めませんでした")
        return
    
    # 出力ディレクトリ
    output_dir = base_dir / "recent_outputs_comparison"
    output_dir.mkdir(exist_ok=True)
    
    print("\n途中式boxedを分析しています...")
    all_stats = {}
    
    for name, responses in all_responses.items():
        stats = analyze_intermediate_boxed(responses, name)
        all_stats[name] = stats
        print(f"\n{name}:")
        print(f"  - 平均Final Answers数: {stats['avg_final_answers']:.2f}")
        print(f"  - 最大Final Answers数: {stats['max_final_answers']}")
        print(f"  - 平均Boxed数: {stats['avg_boxed_count']:.2f}")
        print(f"  - Final Answers数が3個以上: {len(stats['high_count_cases'])}件")
        print(f"  - 途中式boxed使用可能性: {len(stats['intermediate_boxed_cases'])}件")
    
    print("\n可視化しています...")
    visualize_intermediate_boxed(all_stats, output_dir)
    
    print("\nレポートを生成しています...")
    generate_intermediate_boxed_report(all_stats, output_dir)
    
    print(f"\n分析完了！結果は {output_dir} に保存されました。")

if __name__ == "__main__":
    import numpy as np
    main()
