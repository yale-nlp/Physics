#!/usr/bin/env python3
"""
最近追加されたoutputを全て比較するEDAスクリプト
gemini-3.0-pro, gpt-5.2, gpt-4o_rerun を比較
"""

import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from collections import Counter
from typing import Dict, List, Any, Tuple
import itertools

# 日本語フォント設定
plt.rcParams['font.family'] = 'DejaVu Sans'
sns.set_style("whitegrid")
sns.set_palette("husl")

def load_data(base_dir: Path, dataset_path: str) -> Tuple[pd.DataFrame, List[Dict], pd.DataFrame]:
    """データを読み込む"""
    dataset_dir = base_dir / dataset_path
    
    # score.csvを読み込む
    score_df = pd.read_csv(dataset_dir / "score.csv")
    
    # response.jsonlを読み込む
    responses = []
    with open(dataset_dir / "response.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                responses.append(json.loads(line.strip()))
    
    # accuracy.csvを読み込む
    accuracy_df = pd.read_csv(dataset_dir / "accuracy.csv")
    
    return score_df, responses, accuracy_df

def analyze_accuracy_comparison(all_data: Dict[str, Tuple[pd.DataFrame, pd.DataFrame]], output_dir: Path):
    """精度の比較分析"""
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # データを準備
    model_names = list(all_data.keys())
    score_dfs = {name: all_data[name][0] for name in model_names}
    accuracy_dfs = {name: all_data[name][1] for name in model_names}
    
    # 1. ヒストグラム比較
    for name in model_names:
        axes[0, 0].hist(score_dfs[name]['Accuracy'], bins=20, alpha=0.6, 
                       label=name, edgecolor='black')
    axes[0, 0].set_xlabel('Accuracy')
    axes[0, 0].set_ylabel('Frequency')
    axes[0, 0].set_title('Accuracy Distribution Comparison')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)
    
    # 2. ボックスプロット
    data_to_plot = [score_dfs[name]['Accuracy'] for name in model_names]
    bp = axes[0, 1].boxplot(data_to_plot, tick_labels=model_names, patch_artist=True)
    colors = sns.color_palette("husl", len(model_names))
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    axes[0, 1].set_ylabel('Accuracy')
    axes[0, 1].set_title('Accuracy Box Plot Comparison')
    axes[0, 1].grid(True, alpha=0.3)
    axes[0, 1].tick_params(axis='x', rotation=45)
    
    # 3. 累積分布
    for name in model_names:
        sorted_acc = np.sort(score_dfs[name]['Accuracy'])
        p = np.arange(1, len(sorted_acc) + 1) / len(sorted_acc)
        axes[1, 0].plot(sorted_acc, p, label=name, linewidth=2)
    axes[1, 0].set_xlabel('Accuracy')
    axes[1, 0].set_ylabel('Cumulative Probability')
    axes[1, 0].set_title('Cumulative Distribution Function')
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)
    
    # 4. 統計サマリー（Overall Accuracy比較）
    overall_accuracies = [accuracy_dfs[name].iloc[0]['Overall Accuracy'] for name in model_names]
    axes[1, 1].bar(range(len(model_names)), overall_accuracies, color=colors, alpha=0.7)
    axes[1, 1].set_xticks(range(len(model_names)))
    axes[1, 1].set_xticklabels(model_names, rotation=45, ha='right')
    axes[1, 1].set_ylabel('Overall Accuracy')
    axes[1, 1].set_title('Overall Accuracy Comparison')
    axes[1, 1].grid(True, alpha=0.3, axis='y')
    
    # 値をプロット上に表示
    for i, acc in enumerate(overall_accuracies):
        axes[1, 1].text(i, acc + 0.01, f'{acc:.3f}', ha='center', va='bottom')
    
    plt.tight_layout()
    plt.savefig(output_dir / 'accuracy_comparison.png', dpi=300, bbox_inches='tight')
    print(f"Saved: {output_dir / 'accuracy_comparison.png'}")
    plt.close()
    
    return overall_accuracies

def analyze_error_types(all_responses: Dict[str, List[Dict]], output_dir: Path):
    """エラータイプの分析"""
    def count_errors(responses: List[Dict]) -> Dict:
        sympy_errors = 0
        antlr4_errors = 0
        llm_only_correct = 0
        total_entries = len(responses)
        
        for resp in responses:
            if 'equivalency_results' in resp:
                for eq_result in resp['equivalency_results']:
                    error_msg = eq_result.get('error', '')
                    if error_msg:
                        if 'antlr4' in error_msg.lower():
                            antlr4_errors += 1
                            sympy_errors += 1
                        else:
                            sympy_errors += 1
                    if eq_result.get('sympy_result') is None and eq_result.get('llm_result'):
                        llm_only_correct += 1
        
        return {
            'sympy_errors': sympy_errors,
            'antlr4_errors': antlr4_errors,
            'llm_only_correct': llm_only_correct,
            'total_entries': total_entries
        }
    
    error_stats = {}
    for name, responses in all_responses.items():
        error_stats[name] = count_errors(responses)
    
    # 可視化
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    model_names = list(error_stats.keys())
    categories = ['Sympy Errors', 'Antlr4 Errors', 'LLM Only Correct']
    
    x = np.arange(len(categories))
    width = 0.25
    
    for i, name in enumerate(model_names):
        values = [
            error_stats[name]['sympy_errors'],
            error_stats[name]['antlr4_errors'],
            error_stats[name]['llm_only_correct']
        ]
        axes[0].bar(x + i * width, values, width, label=name, alpha=0.7)
    
    axes[0].set_ylabel('Count')
    axes[0].set_title('Error Type Comparison')
    axes[0].set_xticks(x + width)
    axes[0].set_xticklabels(categories, rotation=45, ha='right')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3, axis='y')
    
    # エラー率の比較
    error_rates = {}
    for name in model_names:
        total = error_stats[name]['total_entries']
        error_rates[name] = {
            'sympy_rate': error_stats[name]['sympy_errors'] / total if total > 0 else 0,
            'antlr4_rate': error_stats[name]['antlr4_errors'] / total if total > 0 else 0
        }
    
    x_pos = np.arange(len(model_names))
    sympy_rates = [error_rates[name]['sympy_rate'] for name in model_names]
    antlr4_rates = [error_rates[name]['antlr4_rate'] for name in model_names]
    
    width = 0.35
    axes[1].bar(x_pos - width/2, sympy_rates, width, label='Sympy Error Rate', alpha=0.7)
    axes[1].bar(x_pos + width/2, antlr4_rates, width, label='Antlr4 Error Rate', alpha=0.7)
    axes[1].set_ylabel('Error Rate')
    axes[1].set_title('Error Rate Comparison')
    axes[1].set_xticks(x_pos)
    axes[1].set_xticklabels(model_names, rotation=45, ha='right')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig(output_dir / 'error_analysis.png', dpi=300, bbox_inches='tight')
    print(f"Saved: {output_dir / 'error_analysis.png'}")
    plt.close()
    
    return error_stats

def compare_individual_entries(all_score_dfs: Dict[str, pd.DataFrame], output_dir: Path):
    """個別エントリの比較"""
    # 全てのエントリIDを取得
    all_entry_ids = set()
    for df in all_score_dfs.values():
        all_entry_ids.update(df['Entry ID'].tolist())
    
    # マージ
    merged = pd.DataFrame({'Entry ID': list(all_entry_ids)})
    for name, df in all_score_dfs.items():
        merged = pd.merge(merged, df[['Entry ID', 'Accuracy']], 
                         on='Entry ID', how='outer', suffixes=('', f'_{name}'))
        merged = merged.rename(columns={'Accuracy': f'Accuracy_{name}'})
    
    # 欠損値を0で埋める
    for name in all_score_dfs.keys():
        merged[f'Accuracy_{name}'] = merged[f'Accuracy_{name}'].fillna(0)
    
    # 可視化
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    model_names = list(all_score_dfs.keys())
    
    # 1. 散布図マトリックス（最初の2つ）
    if len(model_names) >= 2:
        axes[0, 0].scatter(merged[f'Accuracy_{model_names[0]}'], 
                          merged[f'Accuracy_{model_names[1]}'], 
                          alpha=0.6, s=50)
        axes[0, 0].plot([0, 1], [0, 1], 'r--', linewidth=2, label='y=x')
        axes[0, 0].set_xlabel(f'{model_names[0]} Accuracy')
        axes[0, 0].set_ylabel(f'{model_names[1]} Accuracy')
        axes[0, 0].set_title(f'{model_names[0]} vs {model_names[1]}')
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3)
    
    # 2. 精度差の分布（最初の2つ）
    if len(model_names) >= 2:
        diff = merged[f'Accuracy_{model_names[1]}'] - merged[f'Accuracy_{model_names[0]}']
        axes[0, 1].hist(diff, bins=30, alpha=0.7, color='green', edgecolor='black')
        axes[0, 1].axvline(x=0, color='red', linestyle='--', linewidth=2)
        axes[0, 1].set_xlabel(f'Accuracy Difference ({model_names[1]} - {model_names[0]})')
        axes[0, 1].set_ylabel('Frequency')
        axes[0, 1].set_title('Accuracy Difference Distribution')
        axes[0, 1].grid(True, alpha=0.3)
    
    # 3. 各モデルの平均精度比較
    mean_accuracies = [merged[f'Accuracy_{name}'].mean() for name in model_names]
    colors = sns.color_palette("husl", len(model_names))
    axes[1, 0].bar(range(len(model_names)), mean_accuracies, color=colors, alpha=0.7)
    axes[1, 0].set_xticks(range(len(model_names)))
    axes[1, 0].set_xticklabels(model_names, rotation=45, ha='right')
    axes[1, 0].set_ylabel('Mean Accuracy')
    axes[1, 0].set_title('Mean Accuracy by Model')
    axes[1, 0].grid(True, alpha=0.3, axis='y')
    for i, acc in enumerate(mean_accuracies):
        axes[1, 0].text(i, acc + 0.01, f'{acc:.3f}', ha='center', va='bottom')
    
    # 4. 統計サマリー
    stats_text = "Statistics Summary:\n\n"
    for name in model_names:
        acc_col = merged[f'Accuracy_{name}']
        stats_text += f"{name}:\n"
        stats_text += f"  Mean: {acc_col.mean():.4f}\n"
        stats_text += f"  Median: {acc_col.median():.4f}\n"
        stats_text += f"  Std: {acc_col.std():.4f}\n"
        stats_text += f"  Min: {acc_col.min():.4f}\n"
        stats_text += f"  Max: {acc_col.max():.4f}\n\n"
    
    axes[1, 1].text(0.1, 0.5, stats_text, fontsize=9, verticalalignment='center',
                    family='monospace', transform=axes[1, 1].transAxes)
    axes[1, 1].axis('off')
    axes[1, 1].set_title('Statistics Summary')
    
    plt.tight_layout()
    plt.savefig(output_dir / 'entry_comparison.png', dpi=300, bbox_inches='tight')
    print(f"Saved: {output_dir / 'entry_comparison.png'}")
    plt.close()
    
    # CSVとして保存
    merged.to_csv(output_dir / 'merged_comparison.csv', index=False)
    print(f"Saved: {output_dir / 'merged_comparison.csv'}")
    
    return merged

def analyze_response_quality(all_responses: Dict[str, List[Dict]], output_dir: Path):
    """レスポンス品質の分析"""
    def extract_metrics(responses: List[Dict]) -> Dict:
        metrics = {
            'avg_final_answers': [],
            'avg_equivalency_results': [],
            'has_sympy_error': 0,
            'has_antlr4_error': 0,
            'total_length': []
        }
        
        for resp in responses:
            if 'final_answers' in resp:
                metrics['avg_final_answers'].append(len(resp['final_answers']))
            if 'equivalency_results' in resp:
                metrics['avg_equivalency_results'].append(len(resp['equivalency_results']))
                has_error = False
                has_antlr4 = False
                for eq_result in resp['equivalency_results']:
                    error_msg = eq_result.get('error', '')
                    if error_msg:
                        has_error = True
                        if 'antlr4' in error_msg.lower():
                            has_antlr4 = True
                if has_error:
                    metrics['has_sympy_error'] += 1
                if has_antlr4:
                    metrics['has_antlr4_error'] += 1
            if 'solution' in resp and resp['solution'] is not None:
                metrics['total_length'].append(len(resp['solution']))
        
        return {
            'avg_final_answers': np.mean(metrics['avg_final_answers']) if metrics['avg_final_answers'] else 0,
            'avg_equivalency_results': np.mean(metrics['avg_equivalency_results']) if metrics['avg_equivalency_results'] else 0,
            'sympy_error_rate': metrics['has_sympy_error'] / len(responses) if responses else 0,
            'antlr4_error_rate': metrics['has_antlr4_error'] / len(responses) if responses else 0,
            'avg_length': np.mean(metrics['total_length']) if metrics['total_length'] else 0
        }
    
    all_metrics = {}
    for name, responses in all_responses.items():
        all_metrics[name] = extract_metrics(responses)
    
    # 可視化
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    model_names = list(all_metrics.keys())
    colors = sns.color_palette("husl", len(model_names))
    
    # 1. 平均final_answers数
    avg_answers = [all_metrics[name]['avg_final_answers'] for name in model_names]
    axes[0, 0].bar(range(len(model_names)), avg_answers, color=colors, alpha=0.7)
    axes[0, 0].set_xticks(range(len(model_names)))
    axes[0, 0].set_xticklabels(model_names, rotation=45, ha='right')
    axes[0, 0].set_ylabel('Average Number of Final Answers')
    axes[0, 0].set_title('Average Final Answers per Entry')
    axes[0, 0].grid(True, alpha=0.3, axis='y')
    
    # 2. 平均equivalency_results数
    avg_equivalency = [all_metrics[name]['avg_equivalency_results'] for name in model_names]
    axes[0, 1].bar(range(len(model_names)), avg_equivalency, color=colors, alpha=0.7)
    axes[0, 1].set_xticks(range(len(model_names)))
    axes[0, 1].set_xticklabels(model_names, rotation=45, ha='right')
    axes[0, 1].set_ylabel('Average Number of Equivalency Results')
    axes[0, 1].set_title('Average Equivalency Results per Entry')
    axes[0, 1].grid(True, alpha=0.3, axis='y')
    
    # 3. Antlr4エラー率
    antlr4_rates = [all_metrics[name]['antlr4_error_rate'] for name in model_names]
    axes[1, 0].bar(range(len(model_names)), antlr4_rates, color=colors, alpha=0.7)
    axes[1, 0].set_xticks(range(len(model_names)))
    axes[1, 0].set_xticklabels(model_names, rotation=45, ha='right')
    axes[1, 0].set_ylabel('Antlr4 Error Rate')
    axes[1, 0].set_title('Antlr4 Error Rate')
    axes[1, 0].grid(True, alpha=0.3, axis='y')
    
    # 4. 平均レスポンス長
    avg_lengths = [all_metrics[name]['avg_length'] for name in model_names]
    axes[1, 1].bar(range(len(model_names)), avg_lengths, color=colors, alpha=0.7)
    axes[1, 1].set_xticks(range(len(model_names)))
    axes[1, 1].set_xticklabels(model_names, rotation=45, ha='right')
    axes[1, 1].set_ylabel('Average Response Length (characters)')
    axes[1, 1].set_title('Average Response Length')
    axes[1, 1].grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig(output_dir / 'response_quality.png', dpi=300, bbox_inches='tight')
    print(f"Saved: {output_dir / 'response_quality.png'}")
    plt.close()
    
    return all_metrics

def generate_summary_report(all_data: Dict[str, Tuple[pd.DataFrame, List[Dict], pd.DataFrame]],
                           overall_accuracies: List[float],
                           error_stats: Dict,
                           all_metrics: Dict,
                           merged: pd.DataFrame,
                           output_dir: Path):
    """サマリーレポートを生成"""
    model_names = list(all_data.keys())
    
    report = f"""
# 最近追加されたOutput比較レポート

## 1. 全体精度比較

"""
    
    for i, name in enumerate(model_names):
        accuracy_df = all_data[name][2]
        report += f"""
### {name}
- Overall Accuracy: {accuracy_df.iloc[0]['Overall Accuracy']:.4f}
- Variance: {accuracy_df.iloc[0]['Variance']:.4f}
- Sympy Error Correct Ratio: {accuracy_df.iloc[0]['Sympy Error Correct Ratio']:.4f}
"""
        if 'Total Tokens' in accuracy_df.columns:
            report += f"- Total Tokens: {accuracy_df.iloc[0]['Total Tokens']:.0f}\n"
            report += f"- Avg Tokens / Problem: {accuracy_df.iloc[0]['Avg Tokens / Problem']:.2f}\n"
    
    report += "\n### 精度ランキング\n"
    sorted_models = sorted(zip(model_names, overall_accuracies), key=lambda x: x[1], reverse=True)
    for rank, (name, acc) in enumerate(sorted_models, 1):
        report += f"{rank}. {name}: {acc:.4f}\n"
    
    report += "\n## 2. 統計サマリー\n\n"
    for name in model_names:
        score_df = all_data[name][0]
        report += f"""
### {name}
- Mean Accuracy: {score_df['Accuracy'].mean():.4f}
- Median Accuracy: {score_df['Accuracy'].median():.4f}
- Std Deviation: {score_df['Accuracy'].std():.4f}
- Min Accuracy: {score_df['Accuracy'].min():.4f}
- Max Accuracy: {score_df['Accuracy'].max():.4f}
- Total Entries: {len(score_df)}
"""
    
    report += "\n## 3. エラー分析\n\n"
    for name in model_names:
        stats = error_stats[name]
        total = stats['total_entries']
        report += f"""
### {name}
- Sympy Errors: {stats['sympy_errors']} ({stats['sympy_errors']/total*100:.2f}%)
- Antlr4 Errors: {stats['antlr4_errors']} ({stats['antlr4_errors']/total*100:.2f}%)
- LLM Only Correct: {stats['llm_only_correct']} 件
"""
    
    report += "\n## 4. レスポンス品質\n\n"
    for name in model_names:
        metrics = all_metrics[name]
        report += f"""
### {name}
- Average Final Answers: {metrics['avg_final_answers']:.2f}
- Average Equivalency Results: {metrics['avg_equivalency_results']:.2f}
- Sympy Error Rate: {metrics['sympy_error_rate']:.4f}
- Antlr4 Error Rate: {metrics['antlr4_error_rate']:.4f}
- Average Response Length: {metrics['avg_length']:.0f} characters
"""
    
    report += "\n## 5. 主な発見\n\n"
    
    # 最高精度のモデル
    best_model = sorted_models[0][0]
    best_acc = sorted_models[0][1]
    report += f"1. **最高精度**: {best_model} ({best_acc:.4f})\n"
    
    # 精度差
    if len(sorted_models) >= 2:
        diff = sorted_models[0][1] - sorted_models[-1][1]
        report += f"2. **精度差**: {diff:.4f} ({diff/sorted_models[-1][1]*100:.2f}%)\n"
    
    # Antlr4エラーの有無
    has_antlr4 = any(error_stats[name]['antlr4_errors'] > 0 for name in model_names)
    if has_antlr4:
        report += "3. **Antlr4エラー**: 一部のモデルでAntlr4エラーが発生\n"
    else:
        report += "3. **Antlr4エラー**: 全てのモデルでAntlr4エラーなし\n"
    
    # エントリ数の比較
    entry_counts = {name: len(all_data[name][0]) for name in model_names}
    if len(set(entry_counts.values())) > 1:
        report += f"4. **エントリ数**: モデル間でエントリ数に差がある\n"
        for name, count in entry_counts.items():
            report += f"   - {name}: {count}件\n"
    
    report += "\n詳細は生成されたグラフとCSVファイルを参照してください。\n"
    
    with open(output_dir / 'comparison_report.md', 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"Saved: {output_dir / 'comparison_report.md'}")
    print("\n" + "="*80)
    print(report)
    print("="*80)

def main():
    base_dir = Path("/Users/takahashiryoutarou/Desktop/LLM実験/Physics/outputs")
    
    # 最近追加されたoutputの定義
    # データセットパスが異なる可能性があるので、実際のパスを確認
    output_configs = [
        ("gemini-3.0-pro", "gemini-3.0-pro_output/mechanics_dataset"),
        ("gpt-5.2", "gpt-5.2_mechanics_output/mechanics_dataset"),
        ("gpt-4o-rerun", "gpt-4o_mechanics_output_rerun/mechanics_dataset"),
    ]
    
    # データ読み込み
    print("データを読み込んでいます...")
    all_data = {}
    all_responses = {}
    all_score_dfs = {}
    
    for name, dataset_path in output_configs:
        try:
            score_df, responses, accuracy_df = load_data(base_dir, dataset_path)
            all_data[name] = (score_df, responses, accuracy_df)
            all_responses[name] = responses
            all_score_dfs[name] = score_df
            print(f"✓ {name}: {len(responses)}件のエントリを読み込み")
        except Exception as e:
            print(f"✗ {name}: 読み込みエラー - {e}")
            continue
    
    if not all_data:
        print("エラー: データを読み込めませんでした")
        return
    
    # 出力ディレクトリ
    output_dir = base_dir / "recent_outputs_comparison"
    output_dir.mkdir(exist_ok=True)
    
    print("\n精度分布を分析しています...")
    overall_accuracies = analyze_accuracy_comparison(
        {name: (all_data[name][0], all_data[name][2]) for name in all_data.keys()},
        output_dir
    )
    
    print("\nエラータイプを分析しています...")
    error_stats = analyze_error_types(all_responses, output_dir)
    
    print("\n個別エントリを比較しています...")
    merged = compare_individual_entries(all_score_dfs, output_dir)
    
    print("\nレスポンス品質を分析しています...")
    all_metrics = analyze_response_quality(all_responses, output_dir)
    
    print("\nサマリーレポートを生成しています...")
    generate_summary_report(
        all_data, overall_accuracies, error_stats, all_metrics, merged, output_dir
    )
    
    print(f"\n比較完了！結果は {output_dir} に保存されました。")

if __name__ == "__main__":
    main()
