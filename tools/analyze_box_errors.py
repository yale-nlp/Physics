#!/usr/bin/env python3
"""
Boxed形式の回答抽出エラーを分析するスクリプト
"""

import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Dict, List, Any
import re

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

def check_boxed_in_solution(solution: str) -> bool:
    """solutionにboxed形式が含まれているかチェック"""
    if not solution:
        return False
    # 様々なboxed形式をチェック
    patterns = [
        r'\\boxed\{',
        r'\\\[boxed\{',
        r'\\\\\[boxed\{',
        r'boxed\{',
    ]
    for pattern in patterns:
        if re.search(pattern, solution, re.IGNORECASE):
            return True
    return False

def analyze_box_errors(responses: List[Dict], model_name: str) -> Dict:
    """Boxエラーを分析"""
    total = len(responses)
    empty_final_answers = 0
    has_solution = 0
    has_boxed_in_solution = 0
    no_solution = 0
    solution_lengths = []
    boxed_patterns_found = []
    
    for resp in responses:
        final_answers = resp.get('final_answers', [])
        solution = resp.get('solution', '')
        
        # final_answersが空のケース
        if not final_answers or len(final_answers) == 0:
            empty_final_answers += 1
            
            # solutionの有無をチェック
            if solution:
                has_solution += 1
                solution_lengths.append(len(solution))
                
                # boxed形式が含まれているかチェック
                if check_boxed_in_solution(solution):
                    has_boxed_in_solution += 1
                    # どのパターンが見つかったか記録
                    if re.search(r'\\boxed\{', solution):
                        boxed_patterns_found.append('\\boxed{')
                    elif re.search(r'\\\[boxed\{', solution):
                        boxed_patterns_found.append('\\[boxed{')
                    elif re.search(r'\\\\\[boxed\{', solution):
                        boxed_patterns_found.append('\\\\[boxed{')
                    else:
                        boxed_patterns_found.append('other')
            else:
                no_solution += 1
    
    return {
        'model_name': model_name,
        'total_entries': total,
        'empty_final_answers': empty_final_answers,
        'empty_rate': empty_final_answers / total if total > 0 else 0,
        'has_solution_but_empty': has_solution,
        'has_boxed_in_solution': has_boxed_in_solution,
        'no_solution': no_solution,
        'solution_lengths': solution_lengths,
        'boxed_patterns_found': boxed_patterns_found,
        'avg_solution_length': sum(solution_lengths) / len(solution_lengths) if solution_lengths else 0
    }

def analyze_solution_samples(responses: List[Dict], model_name: str, num_samples: int = 5) -> List[Dict]:
    """Boxエラーが発生したケースのサンプルを取得"""
    samples = []
    count = 0
    
    for resp in responses:
        if count >= num_samples:
            break
        final_answers = resp.get('final_answers', [])
        solution = resp.get('solution', '')
        
        if not final_answers or len(final_answers) == 0:
            samples.append({
                'id': resp.get('id', 'unknown'),
                'has_solution': bool(solution),
                'solution_length': len(solution) if solution else 0,
                'has_boxed': check_boxed_in_solution(solution) if solution else False,
                'solution_preview': solution[:200] + '...' if solution and len(solution) > 200 else solution
            })
            count += 1
    
    return samples

def visualize_box_errors(all_stats: Dict[str, Dict], output_dir: Path):
    """Boxエラーの可視化"""
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    model_names = list(all_stats.keys())
    
    # 1. 空のfinal_answersの割合
    empty_rates = [all_stats[name]['empty_rate'] for name in model_names]
    colors = sns.color_palette("husl", len(model_names))
    axes[0, 0].bar(range(len(model_names)), empty_rates, color=colors, alpha=0.7)
    axes[0, 0].set_xticks(range(len(model_names)))
    axes[0, 0].set_xticklabels(model_names, rotation=45, ha='right')
    axes[0, 0].set_ylabel('Empty Final Answers Rate')
    axes[0, 0].set_title('Box Extraction Error Rate')
    axes[0, 0].grid(True, alpha=0.3, axis='y')
    for i, rate in enumerate(empty_rates):
        axes[0, 0].text(i, rate + 0.01, f'{rate:.3f}', ha='center', va='bottom')
    
    # 2. 空のfinal_answersの内訳
    has_solution_counts = [all_stats[name]['has_solution_but_empty'] for name in model_names]
    has_boxed_counts = [all_stats[name]['has_boxed_in_solution'] for name in model_names]
    no_solution_counts = [all_stats[name]['no_solution'] for name in model_names]
    
    x = np.arange(len(model_names))
    width = 0.25
    
    axes[0, 1].bar(x - width, has_solution_counts, width, label='Has Solution', alpha=0.7)
    axes[0, 1].bar(x, has_boxed_counts, width, label='Has Boxed in Solution', alpha=0.7)
    axes[0, 1].bar(x + width, no_solution_counts, width, label='No Solution', alpha=0.7)
    axes[0, 1].set_xticks(x)
    axes[0, 1].set_xticklabels(model_names, rotation=45, ha='right')
    axes[0, 1].set_ylabel('Count')
    axes[0, 1].set_title('Empty Final Answers Breakdown')
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3, axis='y')
    
    # 3. solution長の分布（空のfinal_answersの場合）
    for i, name in enumerate(model_names):
        lengths = all_stats[name]['solution_lengths']
        if lengths:
            axes[1, 0].hist(lengths, bins=20, alpha=0.6, label=name, edgecolor='black')
    axes[1, 0].set_xlabel('Solution Length (characters)')
    axes[1, 0].set_ylabel('Frequency')
    axes[1, 0].set_title('Solution Length Distribution (Empty Final Answers)')
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)
    
    # 4. boxedパターンの分布
    pattern_counts = {}
    for name in model_names:
        patterns = all_stats[name]['boxed_patterns_found']
        for pattern in patterns:
            if pattern not in pattern_counts:
                pattern_counts[pattern] = {}
            pattern_counts[pattern][name] = pattern_counts[pattern].get(name, 0) + 1
    
    if pattern_counts:
        patterns = list(pattern_counts.keys())
        pattern_data = []
        for pattern in patterns:
            row = [pattern_counts[pattern].get(name, 0) for name in model_names]
            pattern_data.append(row)
        
        x = np.arange(len(model_names))
        width = 0.8 / len(patterns)
        for i, pattern in enumerate(patterns):
            axes[1, 1].bar(x + i * width, pattern_data[i], width, label=pattern, alpha=0.7)
        axes[1, 1].set_xticks(x + width * (len(patterns) - 1) / 2)
        axes[1, 1].set_xticklabels(model_names, rotation=45, ha='right')
        axes[1, 1].set_ylabel('Count')
        axes[1, 1].set_title('Boxed Patterns Found in Solutions')
        axes[1, 1].legend()
        axes[1, 1].grid(True, alpha=0.3, axis='y')
    else:
        axes[1, 1].text(0.5, 0.5, 'No boxed patterns found', 
                        ha='center', va='center', transform=axes[1, 1].transAxes)
        axes[1, 1].set_title('Boxed Patterns Found in Solutions')
    
    plt.tight_layout()
    plt.savefig(output_dir / 'box_error_analysis.png', dpi=300, bbox_inches='tight')
    print(f"Saved: {output_dir / 'box_error_analysis.png'}")
    plt.close()

def generate_box_error_report(all_stats: Dict[str, Dict], all_samples: Dict[str, List[Dict]], output_dir: Path):
    """Boxエラーのレポートを生成"""
    report = f"""
# Boxed形式の回答抽出エラー分析レポート

## 1. エラー統計

"""
    
    for name in all_stats.keys():
        stats = all_stats[name]
        report += f"""
### {name}
- 総エントリ数: {stats['total_entries']}
- 空のfinal_answers: {stats['empty_final_answers']} ({stats['empty_rate']*100:.2f}%)
- solutionあり（空のfinal_answers）: {stats['has_solution_but_empty']}
- solutionにboxed形式あり: {stats['has_boxed_in_solution']}
- solutionなし: {stats['no_solution']}
- 平均solution長（空のfinal_answers）: {stats['avg_solution_length']:.0f} 文字
"""
    
    report += "\n## 2. エラーケースのサンプル\n\n"
    
    for name in all_samples.keys():
        samples = all_samples[name]
        report += f"### {name}\n\n"
        for i, sample in enumerate(samples, 1):
            report += f"{i}. Entry ID: {sample['id']}\n"
            report += f"   - Solutionあり: {sample['has_solution']}\n"
            report += f"   - Solution長: {sample['solution_length']} 文字\n"
            report += f"   - Boxed形式あり: {sample['has_boxed']}\n"
            if sample['solution_preview']:
                report += f"   - Solution preview: {sample['solution_preview'][:100]}...\n"
            report += "\n"
    
    report += "\n## 3. 主な発見\n\n"
    
    # エラー率の比較
    error_rates = {name: all_stats[name]['empty_rate'] for name in all_stats.keys()}
    sorted_models = sorted(error_rates.items(), key=lambda x: x[1], reverse=True)
    
    report += f"1. **エラー率ランキング**:\n"
    for rank, (name, rate) in enumerate(sorted_models, 1):
        report += f"   {rank}. {name}: {rate*100:.2f}%\n"
    
    # boxed形式が含まれているのに抽出できなかったケース
    report += "\n2. **Boxed形式が含まれているのに抽出できなかったケース**:\n"
    for name in all_stats.keys():
        has_boxed = all_stats[name]['has_boxed_in_solution']
        if has_boxed > 0:
            report += f"   - {name}: {has_boxed}件（抽出ロジックの改善が必要な可能性）\n"
    
    # solutionがないケース
    report += "\n3. **Solutionがないケース**:\n"
    for name in all_stats.keys():
        no_solution = all_stats[name]['no_solution']
        if no_solution > 0:
            report += f"   - {name}: {no_solution}件（LLMが回答を生成できなかった）\n"
    
    report += "\n詳細は生成されたグラフとサンプルを参照してください。\n"
    
    with open(output_dir / 'box_error_report.md', 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"Saved: {output_dir / 'box_error_report.md'}")
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
    
    print("\nBoxエラーを分析しています...")
    all_stats = {}
    all_samples = {}
    
    for name, responses in all_responses.items():
        stats = analyze_box_errors(responses, name)
        all_stats[name] = stats
        samples = analyze_solution_samples(responses, name, num_samples=10)
        all_samples[name] = samples
        print(f"\n{name}:")
        print(f"  - 空のfinal_answers: {stats['empty_final_answers']} ({stats['empty_rate']*100:.2f}%)")
        print(f"  - solutionあり（空のfinal_answers）: {stats['has_solution_but_empty']}")
        print(f"  - solutionにboxed形式あり: {stats['has_boxed_in_solution']}")
        print(f"  - solutionなし: {stats['no_solution']}")
    
    print("\n可視化しています...")
    visualize_box_errors(all_stats, output_dir)
    
    print("\nレポートを生成しています...")
    generate_box_error_report(all_stats, all_samples, output_dir)
    
    print(f"\n分析完了！結果は {output_dir} に保存されました。")

if __name__ == "__main__":
    import numpy as np
    main()
