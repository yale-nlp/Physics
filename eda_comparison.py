#!/usr/bin/env python3
"""
EDAスクリプト: gpt-4o_mechanics_outputとgpt-4o_outputの精度差の原因分析
"""

import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from collections import Counter
import re

# 日本語フォント設定
plt.rcParams['font.family'] = 'DejaVu Sans'
sns.set_style("whitegrid")

def load_data(base_dir, dataset_name):
    """データを読み込む"""
    dataset_dir = Path(base_dir) / dataset_name
    
    # score.csvを読み込む
    score_df = pd.read_csv(dataset_dir / "score.csv")
    
    # response.jsonlを読み込む
    responses = []
    with open(dataset_dir / "response.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            responses.append(json.loads(line.strip()))
    
    # accuracy.csvを読み込む
    accuracy_df = pd.read_csv(dataset_dir / "accuracy.csv")
    
    return score_df, responses, accuracy_df

def analyze_accuracy_distribution(score_df_mech, score_df_orig, output_dir):
    """精度分布の分析"""
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    
    # 1. ヒストグラム比較
    axes[0, 0].hist(score_df_mech['Accuracy'], bins=20, alpha=0.7, label='gpt-4o_mechanics', color='red', edgecolor='black')
    axes[0, 0].hist(score_df_orig['Accuracy'], bins=20, alpha=0.7, label='gpt-4o', color='blue', edgecolor='black')
    axes[0, 0].set_xlabel('Accuracy')
    axes[0, 0].set_ylabel('Frequency')
    axes[0, 0].set_title('Accuracy Distribution Comparison')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)
    
    # 2. ボックスプロット
    data_to_plot = [score_df_mech['Accuracy'], score_df_orig['Accuracy']]
    axes[0, 1].boxplot(data_to_plot, labels=['gpt-4o_mechanics', 'gpt-4o'])
    axes[0, 1].set_ylabel('Accuracy')
    axes[0, 1].set_title('Accuracy Box Plot Comparison')
    axes[0, 1].grid(True, alpha=0.3)
    
    # 3. 累積分布
    sorted_mech = np.sort(score_df_mech['Accuracy'])
    sorted_orig = np.sort(score_df_orig['Accuracy'])
    axes[1, 0].plot(sorted_mech, np.arange(len(sorted_mech))/len(sorted_mech), 
                    label='gpt-4o_mechanics', linewidth=2)
    axes[1, 0].plot(sorted_orig, np.arange(len(sorted_orig))/len(sorted_orig), 
                    label='gpt-4o', linewidth=2)
    axes[1, 0].set_xlabel('Accuracy')
    axes[1, 0].set_ylabel('Cumulative Probability')
    axes[1, 0].set_title('Cumulative Distribution Function')
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)
    
    # 4. 統計サマリー
    stats_text = f"""
    gpt-4o_mechanics:
    Mean: {score_df_mech['Accuracy'].mean():.4f}
    Median: {score_df_mech['Accuracy'].median():.4f}
    Std: {score_df_mech['Accuracy'].std():.4f}
    Min: {score_df_mech['Accuracy'].min():.4f}
    Max: {score_df_mech['Accuracy'].max():.4f}
    
    gpt-4o:
    Mean: {score_df_orig['Accuracy'].mean():.4f}
    Median: {score_df_orig['Accuracy'].median():.4f}
    Std: {score_df_orig['Accuracy'].std():.4f}
    Min: {score_df_orig['Accuracy'].min():.4f}
    Max: {score_df_orig['Accuracy'].max():.4f}
    """
    axes[1, 1].text(0.1, 0.5, stats_text, fontsize=10, verticalalignment='center',
                    family='monospace', transform=axes[1, 1].transAxes)
    axes[1, 1].axis('off')
    axes[1, 1].set_title('Statistics Summary')
    
    plt.tight_layout()
    plt.savefig(output_dir / 'accuracy_distribution.png', dpi=300, bbox_inches='tight')
    print(f"Saved: {output_dir / 'accuracy_distribution.png'}")
    plt.close()

def analyze_error_types(responses_mech, responses_orig, output_dir):
    """エラータイプの分析"""
    def count_errors(responses):
        sympy_errors = 0
        llm_only_correct = 0
        total_entries = len(responses)
        
        for resp in responses:
            if 'equivalency_results' in resp:
                for eq_result in resp['equivalency_results']:
                    if eq_result.get('error'):
                        if 'antlr4' in eq_result.get('error', '').lower():
                            sympy_errors += 1
                    if eq_result.get('sympy_result') is None and eq_result.get('llm_result'):
                        llm_only_correct += 1
        
        return {
            'sympy_errors': sympy_errors,
            'llm_only_correct': llm_only_correct,
            'total_entries': total_entries
        }
    
    errors_mech = count_errors(responses_mech)
    errors_orig = count_errors(responses_orig)
    
    # エラー統計の可視化
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    # Sympyエラーの比較
    categories = ['Sympy Errors', 'LLM Only Correct']
    mech_values = [errors_mech['sympy_errors'], errors_mech['llm_only_correct']]
    orig_values = [errors_orig['sympy_errors'], errors_orig['llm_only_correct']]
    
    x = np.arange(len(categories))
    width = 0.35
    
    axes[0].bar(x - width/2, mech_values, width, label='gpt-4o_mechanics', color='red', alpha=0.7)
    axes[0].bar(x + width/2, orig_values, width, label='gpt-4o', color='blue', alpha=0.7)
    axes[0].set_ylabel('Count')
    axes[0].set_title('Error Type Comparison')
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(categories)
    axes[0].legend()
    axes[0].grid(True, alpha=0.3, axis='y')
    
    # エラー率の比較
    mech_error_rate = errors_mech['sympy_errors'] / errors_mech['total_entries'] if errors_mech['total_entries'] > 0 else 0
    orig_error_rate = errors_orig['sympy_errors'] / errors_orig['total_entries'] if errors_orig['total_entries'] > 0 else 0
    
    axes[1].bar(['gpt-4o_mechanics', 'gpt-4o'], 
                [mech_error_rate, orig_error_rate],
                color=['red', 'blue'], alpha=0.7)
    axes[1].set_ylabel('Sympy Error Rate')
    axes[1].set_title('Sympy Error Rate Comparison')
    axes[1].grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig(output_dir / 'error_analysis.png', dpi=300, bbox_inches='tight')
    print(f"Saved: {output_dir / 'error_analysis.png'}")
    plt.close()
    
    return errors_mech, errors_orig

def compare_individual_entries(score_df_mech, score_df_orig, output_dir):
    """個別エントリの比較"""
    # マージして比較
    merged = pd.merge(score_df_mech, score_df_orig, on='Entry ID', suffixes=('_mech', '_orig'))
    
    # 精度差を計算
    merged['Accuracy_Diff'] = merged['Accuracy_orig'] - merged['Accuracy_mech']
    
    # 精度が大きく異なるエントリを特定
    large_diff = merged[abs(merged['Accuracy_Diff']) > 0.3].sort_values('Accuracy_Diff', ascending=False)
    
    # 可視化
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    
    # 1. 散布図: 両方の精度
    axes[0, 0].scatter(merged['Accuracy_mech'], merged['Accuracy_orig'], alpha=0.6, s=50)
    axes[0, 0].plot([0, 1], [0, 1], 'r--', linewidth=2, label='y=x')
    axes[0, 0].set_xlabel('gpt-4o_mechanics Accuracy')
    axes[0, 0].set_ylabel('gpt-4o Accuracy')
    axes[0, 0].set_title('Accuracy Comparison Scatter Plot')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)
    
    # 2. 精度差の分布
    axes[0, 1].hist(merged['Accuracy_Diff'], bins=30, alpha=0.7, color='green', edgecolor='black')
    axes[0, 1].axvline(x=0, color='red', linestyle='--', linewidth=2)
    axes[0, 1].set_xlabel('Accuracy Difference (gpt-4o - gpt-4o_mechanics)')
    axes[0, 1].set_ylabel('Frequency')
    axes[0, 1].set_title('Accuracy Difference Distribution')
    axes[0, 1].grid(True, alpha=0.3)
    
    # 3. 精度差が大きいエントリ（上位10件）
    top_diff = large_diff.head(10)
    axes[1, 0].barh(range(len(top_diff)), top_diff['Accuracy_Diff'], color='orange', alpha=0.7)
    axes[1, 0].set_yticks(range(len(top_diff)))
    axes[1, 0].set_yticklabels(top_diff['Entry ID'], fontsize=8)
    axes[1, 0].set_xlabel('Accuracy Difference')
    axes[1, 0].set_title('Top 10 Entries with Largest Accuracy Difference')
    axes[1, 0].grid(True, alpha=0.3, axis='x')
    
    # 4. カテゴリ別の精度差
    def extract_category(entry_id):
        if '/' in entry_id:
            return entry_id.split('/')[0]
        return 'Other'
    
    merged['Category'] = merged['Entry ID'].apply(extract_category)
    category_diff = merged.groupby('Category')['Accuracy_Diff'].mean().sort_values(ascending=False)
    
    axes[1, 1].bar(range(len(category_diff)), category_diff.values, color='purple', alpha=0.7)
    axes[1, 1].set_xticks(range(len(category_diff)))
    axes[1, 1].set_xticklabels(category_diff.index, rotation=45, ha='right', fontsize=8)
    axes[1, 1].set_ylabel('Mean Accuracy Difference')
    axes[1, 1].set_title('Accuracy Difference by Category')
    axes[1, 1].grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig(output_dir / 'entry_comparison.png', dpi=300, bbox_inches='tight')
    print(f"Saved: {output_dir / 'entry_comparison.png'}")
    plt.close()
    
    # CSVとして保存
    large_diff.to_csv(output_dir / 'large_accuracy_diff.csv', index=False)
    print(f"Saved: {output_dir / 'large_accuracy_diff.csv'}")
    
    return merged, large_diff

def analyze_response_quality(responses_mech, responses_orig, output_dir):
    """レスポンス品質の分析"""
    def extract_metrics(responses):
        metrics = {
            'avg_final_answers': [],
            'avg_equivalency_results': [],
            'has_sympy_error': 0,
            'total_length': []
        }
        
        for resp in responses:
            if 'final_answers' in resp:
                metrics['avg_final_answers'].append(len(resp['final_answers']))
            if 'equivalency_results' in resp:
                metrics['avg_equivalency_results'].append(len(resp['equivalency_results']))
                # Sympyエラーのチェック
                for eq_result in resp['equivalency_results']:
                    if eq_result.get('error') and 'antlr4' in eq_result.get('error', '').lower():
                        metrics['has_sympy_error'] += 1
                        break
            if 'solution' in resp:
                metrics['total_length'].append(len(resp['solution']))
        
        return {
            'avg_final_answers': np.mean(metrics['avg_final_answers']) if metrics['avg_final_answers'] else 0,
            'avg_equivalency_results': np.mean(metrics['avg_equivalency_results']) if metrics['avg_equivalency_results'] else 0,
            'sympy_error_rate': metrics['has_sympy_error'] / len(responses) if responses else 0,
            'avg_length': np.mean(metrics['total_length']) if metrics['total_length'] else 0
        }
    
    metrics_mech = extract_metrics(responses_mech)
    metrics_orig = extract_metrics(responses_orig)
    
    # 可視化
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # 1. 平均final_answers数
    axes[0, 0].bar(['gpt-4o_mechanics', 'gpt-4o'],
                   [metrics_mech['avg_final_answers'], metrics_orig['avg_final_answers']],
                   color=['red', 'blue'], alpha=0.7)
    axes[0, 0].set_ylabel('Average Number of Final Answers')
    axes[0, 0].set_title('Average Final Answers per Entry')
    axes[0, 0].grid(True, alpha=0.3, axis='y')
    
    # 2. 平均equivalency_results数
    axes[0, 1].bar(['gpt-4o_mechanics', 'gpt-4o'],
                   [metrics_mech['avg_equivalency_results'], metrics_orig['avg_equivalency_results']],
                   color=['red', 'blue'], alpha=0.7)
    axes[0, 1].set_ylabel('Average Number of Equivalency Results')
    axes[0, 1].set_title('Average Equivalency Results per Entry')
    axes[0, 1].grid(True, alpha=0.3, axis='y')
    
    # 3. Sympyエラー率
    axes[1, 0].bar(['gpt-4o_mechanics', 'gpt-4o'],
                   [metrics_mech['sympy_error_rate'], metrics_orig['sympy_error_rate']],
                   color=['red', 'blue'], alpha=0.7)
    axes[1, 0].set_ylabel('Sympy Error Rate')
    axes[1, 0].set_title('Sympy Error Rate')
    axes[1, 0].grid(True, alpha=0.3, axis='y')
    
    # 4. 平均レスポンス長
    axes[1, 1].bar(['gpt-4o_mechanics', 'gpt-4o'],
                   [metrics_mech['avg_length'], metrics_orig['avg_length']],
                   color=['red', 'blue'], alpha=0.7)
    axes[1, 1].set_ylabel('Average Response Length (characters)')
    axes[1, 1].set_title('Average Response Length')
    axes[1, 1].grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig(output_dir / 'response_quality.png', dpi=300, bbox_inches='tight')
    print(f"Saved: {output_dir / 'response_quality.png'}")
    plt.close()
    
    return metrics_mech, metrics_orig

def generate_summary_report(score_df_mech, score_df_orig, accuracy_df_mech, accuracy_df_orig,
                           errors_mech, errors_orig, merged, metrics_mech, metrics_orig, output_dir):
    """サマリーレポートを生成"""
    report = f"""
# EDA Report: gpt-4o_mechanics_output vs gpt-4o_output

## 1. 全体精度比較

### gpt-4o_mechanics_output
- Overall Accuracy: {accuracy_df_mech.iloc[0]['Overall Accuracy']:.4f}
- Variance: {accuracy_df_mech.iloc[0]['Variance']:.4f}
- Sympy Error Correct Ratio: {accuracy_df_mech.iloc[0]['Sympy Error Correct Ratio']:.4f}

### gpt-4o_output
- Overall Accuracy: {accuracy_df_orig.iloc[0]['Overall Accuracy']:.4f}
- Variance: {accuracy_df_orig.iloc[0]['Variance']:.4f}
- Sympy Error Correct Ratio: {accuracy_df_orig.iloc[0]['Sympy Error Correct Ratio']:.4f}

### 精度差
- **精度差**: {accuracy_df_orig.iloc[0]['Overall Accuracy'] - accuracy_df_mech.iloc[0]['Overall Accuracy']:.4f} ({((accuracy_df_orig.iloc[0]['Overall Accuracy'] - accuracy_df_mech.iloc[0]['Overall Accuracy']) / accuracy_df_mech.iloc[0]['Overall Accuracy'] * 100):.2f}% 低い)

## 2. 統計サマリー

### gpt-4o_mechanics_output
- Mean Accuracy: {score_df_mech['Accuracy'].mean():.4f}
- Median Accuracy: {score_df_mech['Accuracy'].median():.4f}
- Std Deviation: {score_df_mech['Accuracy'].std():.4f}
- Min Accuracy: {score_df_mech['Accuracy'].min():.4f}
- Max Accuracy: {score_df_mech['Accuracy'].max():.4f}

### gpt-4o_output
- Mean Accuracy: {score_df_orig['Accuracy'].mean():.4f}
- Median Accuracy: {score_df_orig['Accuracy'].median():.4f}
- Std Deviation: {score_df_orig['Accuracy'].std():.4f}
- Min Accuracy: {score_df_orig['Accuracy'].min():.4f}
- Max Accuracy: {score_df_orig['Accuracy'].max():.4f}

## 3. エラー分析

### Sympyエラー
- gpt-4o_mechanics: {errors_mech['sympy_errors']} エラー ({errors_mech['sympy_errors']/errors_mech['total_entries']*100:.2f}%)
- gpt-4o: {errors_orig['sympy_errors']} エラー ({errors_orig['sympy_errors']/errors_orig['total_entries']*100:.2f}%)

### LLMのみで正解
- gpt-4o_mechanics: {errors_mech['llm_only_correct']} 件
- gpt-4o: {errors_orig['llm_only_correct']} 件

## 4. レスポンス品質

### gpt-4o_mechanics_output
- Average Final Answers: {metrics_mech['avg_final_answers']:.2f}
- Average Equivalency Results: {metrics_mech['avg_equivalency_results']:.2f}
- Sympy Error Rate: {metrics_mech['sympy_error_rate']:.4f}
- Average Response Length: {metrics_mech['avg_length']:.0f} characters

### gpt-4o_output
- Average Final Answers: {metrics_orig['avg_final_answers']:.2f}
- Average Equivalency Results: {metrics_orig['avg_equivalency_results']:.2f}
- Sympy Error Rate: {metrics_orig['sympy_error_rate']:.4f}
- Average Response Length: {metrics_orig['avg_length']:.0f} characters

## 5. 個別エントリ分析

### 精度差が大きいエントリ（上位5件）
"""
    
    large_diff = merged[abs(merged['Accuracy_Diff']) > 0.3].sort_values('Accuracy_Diff', ascending=False)
    for idx, row in large_diff.head(5).iterrows():
        report += f"\n- **{row['Entry ID']}**: {row['Accuracy_mech']:.4f} → {row['Accuracy_orig']:.4f} (差: {row['Accuracy_Diff']:.4f})\n"
    
    report += f"""
## 6. 主な発見

1. **精度差**: gpt-4o_mechanics_outputはgpt-4o_outputより{accuracy_df_orig.iloc[0]['Overall Accuracy'] - accuracy_df_mech.iloc[0]['Overall Accuracy']:.4f} ({((accuracy_df_orig.iloc[0]['Overall Accuracy'] - accuracy_df_mech.iloc[0]['Overall Accuracy']) / accuracy_df_mech.iloc[0]['Overall Accuracy'] * 100):.2f}%)低い

2. **Sympyエラー**: 両方のデータセットでSympyエラーが発生しているが、gpt-4o_outputの方がSympy Error Correct Ratioが高い

3. **精度分布**: 精度の分布に違いがある可能性がある

4. **個別エントリ**: {len(large_diff)}個のエントリで精度差が0.3以上
"""
    
    with open(output_dir / 'eda_report.md', 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"Saved: {output_dir / 'eda_report.md'}")
    print("\n" + "="*80)
    print(report)
    print("="*80)

def main():
    base_dir = Path("/Users/takahashiryoutarou/Desktop/LLM実験/Physics/outputs")
    
    # データ読み込み
    print("Loading data...")
    score_df_mech, responses_mech, accuracy_df_mech = load_data(
        base_dir, "gpt-4o_mechanics_output/mechanics_dataset"
    )
    score_df_orig, responses_orig, accuracy_df_orig = load_data(
        base_dir, "gpt-4o_output/mechanics_dataset"
    )
    
    # 出力ディレクトリ
    output_dir = base_dir / "eda_comparison"
    output_dir.mkdir(exist_ok=True)
    
    print("\nAnalyzing accuracy distribution...")
    analyze_accuracy_distribution(score_df_mech, score_df_orig, output_dir)
    
    print("\nAnalyzing error types...")
    errors_mech, errors_orig = analyze_error_types(responses_mech, responses_orig, output_dir)
    
    print("\nComparing individual entries...")
    merged, large_diff = compare_individual_entries(score_df_mech, score_df_orig, output_dir)
    
    print("\nAnalyzing response quality...")
    metrics_mech, metrics_orig = analyze_response_quality(responses_mech, responses_orig, output_dir)
    
    print("\nGenerating summary report...")
    generate_summary_report(
        score_df_mech, score_df_orig, accuracy_df_mech, accuracy_df_orig,
        errors_mech, errors_orig, merged, metrics_mech, metrics_orig, output_dir
    )
    
    print("\nEDA完了!")

if __name__ == "__main__":
    main()
