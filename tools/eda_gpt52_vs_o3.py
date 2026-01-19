"""
GPT-5.2とo3-miniの力学データセット評価結果のEDA
精度差の原因を分析する
"""

import json
import csv
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from collections import Counter
import numpy as np
from typing import Dict, List, Any

# 日本語フォント設定
plt.rcParams['font.family'] = 'DejaVu Sans'
sns.set_style("whitegrid")
sns.set_palette("husl")

def load_jsonl(file_path: str) -> List[Dict[str, Any]]:
    """JSONLファイルを読み込む"""
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    return data

def load_score_csv(file_path: str) -> pd.DataFrame:
    """スコアCSVファイルを読み込む"""
    return pd.read_csv(file_path)

def analyze_accuracy_distribution(df_gpt52: pd.DataFrame, df_o3: pd.DataFrame, output_dir: Path):
    """精度分布の比較分析"""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # 1. 精度のヒストグラム
    axes[0, 0].hist(df_gpt52['Accuracy'], bins=20, alpha=0.7, label='GPT-5.2', color='blue')
    axes[0, 0].hist(df_o3['Accuracy'], bins=20, alpha=0.7, label='o3-mini', color='orange')
    axes[0, 0].set_xlabel('Accuracy')
    axes[0, 0].set_ylabel('Frequency')
    axes[0, 0].set_title('Accuracy Distribution')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)
    
    # 2. 箱ひげ図
    data_to_plot = [df_gpt52['Accuracy'], df_o3['Accuracy']]
    bp = axes[0, 1].boxplot(data_to_plot, labels=['GPT-5.2', 'o3-mini'], patch_artist=True)
    bp['boxes'][0].set_facecolor('blue')
    bp['boxes'][1].set_facecolor('orange')
    axes[0, 1].set_ylabel('Accuracy')
    axes[0, 1].set_title('Accuracy Box Plot')
    axes[0, 1].grid(True, alpha=0.3)
    
    # 3. 統計サマリー
    stats_gpt52 = df_gpt52['Accuracy'].describe()
    stats_o3 = df_o3['Accuracy'].describe()
    
    stats_text = f"""GPT-5.2 Statistics:
Mean: {stats_gpt52['mean']:.4f}
Median: {stats_gpt52['50%']:.4f}
Std: {stats_gpt52['std']:.4f}
Min: {stats_gpt52['min']:.4f}
Max: {stats_gpt52['max']:.4f}

o3-mini Statistics:
Mean: {stats_o3['mean']:.4f}
Median: {stats_o3['50%']:.4f}
Std: {stats_o3['std']:.4f}
Min: {stats_o3['min']:.4f}
Max: {stats_o3['max']:.4f}"""
    
    axes[1, 0].text(0.1, 0.5, stats_text, fontsize=10, verticalalignment='center',
                    family='monospace', transform=axes[1, 0].transAxes)
    axes[1, 0].axis('off')
    axes[1, 0].set_title('Statistics Summary')
    
    # 4. 累積分布関数
    sorted_gpt52 = np.sort(df_gpt52['Accuracy'])
    sorted_o3 = np.sort(df_o3['Accuracy'])
    p_gpt52 = np.arange(1, len(sorted_gpt52) + 1) / len(sorted_gpt52)
    p_o3 = np.arange(1, len(sorted_o3) + 1) / len(sorted_o3)
    
    axes[1, 1].plot(sorted_gpt52, p_gpt52, label='GPT-5.2', linewidth=2, color='blue')
    axes[1, 1].plot(sorted_o3, p_o3, label='o3-mini', linewidth=2, color='orange')
    axes[1, 1].set_xlabel('Accuracy')
    axes[1, 1].set_ylabel('Cumulative Probability')
    axes[1, 1].set_title('Cumulative Distribution Function')
    axes[1, 1].legend()
    axes[1, 1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'accuracy_distribution.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    return stats_gpt52, stats_o3

def analyze_error_cases(responses_gpt52: List[Dict], responses_o3: List[Dict], output_dir: Path):
    """エラーケースの詳細分析"""
    # エラーケースを抽出
    errors_gpt52 = [r for r in responses_gpt52 if r.get('accuracy', 0) == 0]
    errors_o3 = [r for r in responses_o3 if r.get('accuracy', 0) == 0]
    
    # 両方でエラーになったケース
    error_ids_gpt52 = {r['id'] for r in errors_gpt52}
    error_ids_o3 = {r['id'] for r in errors_o3}
    common_errors = error_ids_gpt52 & error_ids_o3
    gpt52_only_errors = error_ids_gpt52 - error_ids_o3
    o3_only_errors = error_ids_o3 - error_ids_gpt52
    
    # レポート作成
    report = []
    report.append("=" * 80)
    report.append("エラーケース分析")
    report.append("=" * 80)
    report.append(f"\nGPT-5.2のエラー数: {len(errors_gpt52)}")
    report.append(f"o3-miniのエラー数: {len(errors_o3)}")
    report.append(f"\n両方でエラー: {len(common_errors)}")
    report.append(f"GPT-5.2のみエラー: {len(gpt52_only_errors)}")
    report.append(f"o3-miniのみエラー: {len(o3_only_errors)}")
    
    # GPT-5.2のみエラーの詳細分析
    report.append("\n" + "=" * 80)
    report.append("GPT-5.2のみエラーとなった問題（上位10件）")
    report.append("=" * 80)
    
    gpt52_only_details = []
    for r in responses_gpt52:
        if r['id'] in gpt52_only_errors:
            gpt52_only_details.append({
                'id': r['id'],
                'accuracy': r.get('accuracy', 0),
                'num_answers': len(r.get('final_answers', [])),
                'num_equivalency': len(r.get('equivalency_results', []))
            })
    
    gpt52_only_details.sort(key=lambda x: x['id'])
    for i, detail in enumerate(gpt52_only_details[:10], 1):
        report.append(f"{i}. {detail['id']}: accuracy={detail['accuracy']}, "
                     f"answers={detail['num_answers']}, equivalency={detail['num_equivalency']}")
    
    # エラーケースの詳細をJSONに保存
    error_details = {
        'common_errors': list(common_errors),
        'gpt52_only_errors': list(gpt52_only_errors),
        'o3_only_errors': list(o3_only_errors),
        'gpt52_error_details': gpt52_only_details[:20]
    }
    
    with open(output_dir / 'error_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(error_details, f, indent=2, ensure_ascii=False)
    
    return '\n'.join(report)

def analyze_response_characteristics(responses_gpt52: List[Dict], responses_o3: List[Dict], output_dir: Path):
    """レスポンスの特徴分析"""
    # レスポンス長の分析
    gpt52_lengths = []
    gpt52_answer_counts = []
    gpt52_equivalency_counts = []
    
    o3_lengths = []
    o3_answer_counts = []
    o3_equivalency_counts = []
    
    for r in responses_gpt52:
        solution = r.get('solution', '')
        gpt52_lengths.append(len(solution))
        gpt52_answer_counts.append(len(r.get('final_answers', [])))
        gpt52_equivalency_counts.append(len(r.get('equivalency_results', [])))
    
    for r in responses_o3:
        solution = r.get('solution', '')
        o3_lengths.append(len(solution))
        o3_answer_counts.append(len(r.get('final_answers', [])))
        o3_equivalency_counts.append(len(r.get('equivalency_results', [])))
    
    # 可視化
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    
    # 1. レスポンス長の分布
    axes[0, 0].hist(gpt52_lengths, bins=30, alpha=0.7, label='GPT-5.2', color='blue')
    axes[0, 0].hist(o3_lengths, bins=30, alpha=0.7, label='o3-mini', color='orange')
    axes[0, 0].set_xlabel('Response Length (characters)')
    axes[0, 0].set_ylabel('Frequency')
    axes[0, 0].set_title('Response Length Distribution')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)
    
    # 2. 回答数の分布
    axes[0, 1].hist(gpt52_answer_counts, bins=range(0, max(max(gpt52_answer_counts), max(o3_answer_counts)) + 2),
                   alpha=0.7, label='GPT-5.2', color='blue', align='left')
    axes[0, 1].hist(o3_answer_counts, bins=range(0, max(max(gpt52_answer_counts), max(o3_answer_counts)) + 2),
                   alpha=0.7, label='o3-mini', color='orange', align='left')
    axes[0, 1].set_xlabel('Number of Final Answers')
    axes[0, 1].set_ylabel('Frequency')
    axes[0, 1].set_title('Number of Answers Distribution')
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)
    
    # 3. 等価性チェック数の分布
    axes[0, 2].hist(gpt52_equivalency_counts, bins=30, alpha=0.7, label='GPT-5.2', color='blue')
    axes[0, 2].hist(o3_equivalency_counts, bins=30, alpha=0.7, label='o3-mini', color='orange')
    axes[0, 2].set_xlabel('Number of Equivalency Checks')
    axes[0, 2].set_ylabel('Frequency')
    axes[0, 2].set_title('Equivalency Checks Distribution')
    axes[0, 2].legend()
    axes[0, 2].grid(True, alpha=0.3)
    
    # 4. レスポンス長 vs 精度（GPT-5.2）
    if len(gpt52_lengths) > 0:
        df_gpt52_combined = pd.DataFrame({
            'length': gpt52_lengths,
            'accuracy': [r.get('accuracy', 0) for r in responses_gpt52]
        })
        axes[1, 0].scatter(df_gpt52_combined['length'], df_gpt52_combined['accuracy'],
                          alpha=0.5, color='blue', s=20)
        axes[1, 0].set_xlabel('Response Length')
        axes[1, 0].set_ylabel('Accuracy')
        axes[1, 0].set_title('GPT-5.2: Length vs Accuracy')
        axes[1, 0].grid(True, alpha=0.3)
    
    # 5. レスポンス長 vs 精度（o3-mini）
    if len(o3_lengths) > 0:
        df_o3_combined = pd.DataFrame({
            'length': o3_lengths,
            'accuracy': [r.get('accuracy', 0) for r in responses_o3]
        })
        axes[1, 1].scatter(df_o3_combined['length'], df_o3_combined['accuracy'],
                          alpha=0.5, color='orange', s=20)
        axes[1, 1].set_xlabel('Response Length')
        axes[1, 1].set_ylabel('Accuracy')
        axes[1, 1].set_title('o3-mini: Length vs Accuracy')
        axes[1, 1].grid(True, alpha=0.3)
    
    # 6. 統計サマリー
    stats_text = f"""GPT-5.2:
Avg Length: {np.mean(gpt52_lengths):.0f}
Avg Answers: {np.mean(gpt52_answer_counts):.2f}
Avg Equivalency: {np.mean(gpt52_equivalency_counts):.2f}

o3-mini:
Avg Length: {np.mean(o3_lengths):.0f}
Avg Answers: {np.mean(o3_answer_counts):.2f}
Avg Equivalency: {np.mean(o3_equivalency_counts):.2f}"""
    
    axes[1, 2].text(0.1, 0.5, stats_text, fontsize=10, verticalalignment='center',
                    family='monospace', transform=axes[1, 2].transAxes)
    axes[1, 2].axis('off')
    axes[1, 2].set_title('Response Characteristics')
    
    plt.tight_layout()
    plt.savefig(output_dir / 'response_characteristics.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    return {
        'gpt52': {
            'avg_length': np.mean(gpt52_lengths),
            'avg_answers': np.mean(gpt52_answer_counts),
            'avg_equivalency': np.mean(gpt52_equivalency_counts)
        },
        'o3': {
            'avg_length': np.mean(o3_lengths),
            'avg_answers': np.mean(o3_answer_counts),
            'avg_equivalency': np.mean(o3_equivalency_counts)
        }
    }

def analyze_equivalency_results(responses_gpt52: List[Dict], responses_o3: List[Dict], output_dir: Path):
    """等価性チェック結果の詳細分析"""
    gpt52_sympy_errors = 0
    gpt52_llm_correct = 0
    gpt52_total_checks = 0
    
    o3_sympy_errors = 0
    o3_llm_correct = 0
    o3_total_checks = 0
    
    gpt52_error_details = []
    o3_error_details = []
    
    for r in responses_gpt52:
        equivalency_results = r.get('equivalency_results', [])
        gpt52_total_checks += len(equivalency_results)
        
        for eq_result in equivalency_results:
            sympy_result = eq_result.get('sympy_result')
            llm_result = eq_result.get('llm_result')
            error = eq_result.get('error')
            
            if sympy_result is False and llm_result is True:
                gpt52_llm_correct += 1
            if sympy_result is not None and sympy_result is False:
                gpt52_sympy_errors += 1
                if error:
                    gpt52_error_details.append({
                        'id': r['id'],
                        'error': error,
                        'expr1': eq_result.get('input_expressions', {}).get('expr1', ''),
                        'expr2': eq_result.get('input_expressions', {}).get('expr2', '')
                    })
    
    for r in responses_o3:
        equivalency_results = r.get('equivalency_results', [])
        o3_total_checks += len(equivalency_results)
        
        for eq_result in equivalency_results:
            sympy_result = eq_result.get('sympy_result')
            llm_result = eq_result.get('llm_result')
            error = eq_result.get('error')
            
            if sympy_result is False and llm_result is True:
                o3_llm_correct += 1
            if sympy_result is not None and sympy_result is False:
                o3_sympy_errors += 1
                if error:
                    o3_error_details.append({
                        'id': r['id'],
                        'error': error,
                        'expr1': eq_result.get('input_expressions', {}).get('expr1', ''),
                        'expr2': eq_result.get('input_expressions', {}).get('expr2', '')
                    })
    
    # 可視化
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # Sympyエラー率
    categories = ['GPT-5.2', 'o3-mini']
    sympy_error_rates = [
        gpt52_sympy_errors / gpt52_total_checks if gpt52_total_checks > 0 else 0,
        o3_sympy_errors / o3_total_checks if o3_total_checks > 0 else 0
    ]
    llm_correct_rates = [
        gpt52_llm_correct / gpt52_total_checks if gpt52_total_checks > 0 else 0,
        o3_llm_correct / o3_total_checks if o3_total_checks > 0 else 0
    ]
    
    x = np.arange(len(categories))
    width = 0.35
    
    axes[0].bar(x - width/2, sympy_error_rates, width, label='Sympy Error Rate', color='red', alpha=0.7)
    axes[0].bar(x + width/2, llm_correct_rates, width, label='LLM Correct Rate', color='green', alpha=0.7)
    axes[0].set_ylabel('Rate')
    axes[0].set_title('Sympy Error and LLM Correct Rates')
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(categories)
    axes[0].legend()
    axes[0].grid(True, alpha=0.3, axis='y')
    
    # 統計サマリー
    stats_text = f"""GPT-5.2:
Total Checks: {gpt52_total_checks}
Sympy Errors: {gpt52_sympy_errors}
LLM Correct: {gpt52_llm_correct}
Sympy Error Rate: {sympy_error_rates[0]:.4f}
LLM Correct Rate: {llm_correct_rates[0]:.4f}

o3-mini:
Total Checks: {o3_total_checks}
Sympy Errors: {o3_sympy_errors}
LLM Correct: {o3_llm_correct}
Sympy Error Rate: {sympy_error_rates[1]:.4f}
LLM Correct Rate: {llm_correct_rates[1]:.4f}"""
    
    axes[1].text(0.1, 0.5, stats_text, fontsize=10, verticalalignment='center',
                family='monospace', transform=axes[1].transAxes)
    axes[1].axis('off')
    axes[1].set_title('Equivalency Statistics')
    
    plt.tight_layout()
    plt.savefig(output_dir / 'equivalency_analysis.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # エラー詳細を保存
    error_summary = {
        'gpt52': {
            'total_checks': gpt52_total_checks,
            'sympy_errors': gpt52_sympy_errors,
            'llm_correct': gpt52_llm_correct,
            'error_details': gpt52_error_details[:20]
        },
        'o3': {
            'total_checks': o3_total_checks,
            'sympy_errors': o3_sympy_errors,
            'llm_correct': o3_llm_correct,
            'error_details': o3_error_details[:20]
        }
    }
    
    with open(output_dir / 'equivalency_errors.json', 'w', encoding='utf-8') as f:
        json.dump(error_summary, f, indent=2, ensure_ascii=False)
    
    return error_summary

def analyze_token_usage(responses_gpt52: List[Dict], output_dir: Path):
    """トークン使用量の分析（GPT-5.2のみ）"""
    token_data = []
    
    for r in responses_gpt52:
        token_usage = r.get('token_usage')
        if token_usage:
            token_data.append({
                'id': r['id'],
                'prompt_tokens': token_usage.get('prompt_tokens', 0),
                'completion_tokens': token_usage.get('completion_tokens', 0),
                'total_tokens': token_usage.get('total_tokens', 0),
                'accuracy': r.get('accuracy', 0)
            })
    
    if not token_data:
        return None
    
    df_tokens = pd.DataFrame(token_data)
    
    # 可視化
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # 1. トークン数の分布
    axes[0, 0].hist(df_tokens['total_tokens'], bins=30, alpha=0.7, color='blue')
    axes[0, 0].set_xlabel('Total Tokens')
    axes[0, 0].set_ylabel('Frequency')
    axes[0, 0].set_title('Total Tokens Distribution (GPT-5.2)')
    axes[0, 0].grid(True, alpha=0.3)
    
    # 2. トークン数 vs 精度
    axes[0, 1].scatter(df_tokens['total_tokens'], df_tokens['accuracy'], alpha=0.5, s=20)
    axes[0, 1].set_xlabel('Total Tokens')
    axes[0, 1].set_ylabel('Accuracy')
    axes[0, 1].set_title('Tokens vs Accuracy (GPT-5.2)')
    axes[0, 1].grid(True, alpha=0.3)
    
    # 3. Prompt vs Completion tokens
    axes[1, 0].scatter(df_tokens['prompt_tokens'], df_tokens['completion_tokens'], alpha=0.5, s=20)
    axes[1, 0].set_xlabel('Prompt Tokens')
    axes[1, 0].set_ylabel('Completion Tokens')
    axes[1, 0].set_title('Prompt vs Completion Tokens (GPT-5.2)')
    axes[1, 0].grid(True, alpha=0.3)
    
    # 4. 統計サマリー
    stats_text = f"""Token Usage Statistics:
Avg Total: {df_tokens['total_tokens'].mean():.0f}
Avg Prompt: {df_tokens['prompt_tokens'].mean():.0f}
Avg Completion: {df_tokens['completion_tokens'].mean():.0f}
Max Total: {df_tokens['total_tokens'].max():.0f}
Min Total: {df_tokens['total_tokens'].min():.0f}"""
    
    axes[1, 1].text(0.1, 0.5, stats_text, fontsize=10, verticalalignment='center',
                    family='monospace', transform=axes[1, 1].transAxes)
    axes[1, 1].axis('off')
    axes[1, 1].set_title('Token Statistics')
    
    plt.tight_layout()
    plt.savefig(output_dir / 'token_usage.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    return df_tokens.describe()

def generate_summary_report(stats_gpt52: pd.Series, stats_o3: pd.Series, 
                           error_report: str, response_stats: Dict,
                           equivalency_stats: Dict, token_stats: pd.DataFrame | None,
                           output_dir: Path):
    """総合レポートを生成"""
    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("GPT-5.2 vs o3-mini 評価結果比較レポート")
    report_lines.append("=" * 80)
    report_lines.append("")
    
    # 精度比較
    report_lines.append("【精度比較】")
    report_lines.append(f"GPT-5.2: {stats_gpt52['mean']:.4f} (median: {stats_gpt52['50%']:.4f})")
    report_lines.append(f"o3-mini: {stats_o3['mean']:.4f} (median: {stats_o3['50%']:.4f})")
    report_lines.append(f"差: {stats_o3['mean'] - stats_gpt52['mean']:.4f} ({((stats_o3['mean'] - stats_gpt52['mean']) / stats_gpt52['mean'] * 100):.2f}%)")
    report_lines.append("")
    
    # レスポンス特徴
    report_lines.append("【レスポンス特徴】")
    report_lines.append(f"GPT-5.2:")
    report_lines.append(f"  平均長: {response_stats['gpt52']['avg_length']:.0f} 文字")
    report_lines.append(f"  平均回答数: {response_stats['gpt52']['avg_answers']:.2f}")
    report_lines.append(f"  平均等価性チェック数: {response_stats['gpt52']['avg_equivalency']:.2f}")
    report_lines.append(f"o3-mini:")
    report_lines.append(f"  平均長: {response_stats['o3']['avg_length']:.0f} 文字")
    report_lines.append(f"  平均回答数: {response_stats['o3']['avg_answers']:.2f}")
    report_lines.append(f"  平均等価性チェック数: {response_stats['o3']['avg_equivalency']:.2f}")
    report_lines.append("")
    
    # 等価性チェック
    report_lines.append("【等価性チェック結果】")
    gpt52_total = equivalency_stats['gpt52']['total_checks']
    o3_total = equivalency_stats['o3']['total_checks']
    if gpt52_total > 0:
        gpt52_sympy_rate = equivalency_stats['gpt52']['sympy_errors'] / gpt52_total
        gpt52_llm_rate = equivalency_stats['gpt52']['llm_correct'] / gpt52_total
    else:
        gpt52_sympy_rate = 0
        gpt52_llm_rate = 0
    
    if o3_total > 0:
        o3_sympy_rate = equivalency_stats['o3']['sympy_errors'] / o3_total
        o3_llm_rate = equivalency_stats['o3']['llm_correct'] / o3_total
    else:
        o3_sympy_rate = 0
        o3_llm_rate = 0
    
    report_lines.append(f"GPT-5.2:")
    report_lines.append(f"  Sympyエラー率: {gpt52_sympy_rate:.4f}")
    report_lines.append(f"  LLM正解率: {gpt52_llm_rate:.4f}")
    report_lines.append(f"o3-mini:")
    report_lines.append(f"  Sympyエラー率: {o3_sympy_rate:.4f}")
    report_lines.append(f"  LLM正解率: {o3_llm_rate:.4f}")
    report_lines.append("")
    
    # トークン使用量
    if token_stats is not None:
        report_lines.append("【トークン使用量（GPT-5.2のみ）】")
        report_lines.append(f"  平均総トークン数: {token_stats.loc['mean', 'total_tokens']:.0f}")
        report_lines.append(f"  平均プロンプトトークン: {token_stats.loc['mean', 'prompt_tokens']:.0f}")
        report_lines.append(f"  平均完了トークン: {token_stats.loc['mean', 'completion_tokens']:.0f}")
        report_lines.append("")
    
    # エラー分析
    report_lines.append(error_report)
    
    # 結論
    report_lines.append("\n" + "=" * 80)
    report_lines.append("【主な発見】")
    report_lines.append("=" * 80)
    
    if stats_o3['mean'] > stats_gpt52['mean']:
        report_lines.append(f"1. o3-miniの精度がGPT-5.2より{stats_o3['mean'] - stats_gpt52['mean']:.4f}高い")
    
    if response_stats['gpt52']['avg_length'] != response_stats['o3']['avg_length']:
        report_lines.append(f"2. レスポンス長に差がある（GPT-5.2: {response_stats['gpt52']['avg_length']:.0f}, o3-mini: {response_stats['o3']['avg_length']:.0f}）")
    
    if gpt52_sympy_rate != o3_sympy_rate:
        report_lines.append(f"3. Sympyエラー率に差がある（GPT-5.2: {gpt52_sympy_rate:.4f}, o3-mini: {o3_sympy_rate:.4f}）")
    
    report_lines.append("\n詳細は生成されたグラフとJSONファイルを参照してください。")
    
    report_text = '\n'.join(report_lines)
    
    with open(output_dir / 'summary_report.txt', 'w', encoding='utf-8') as f:
        f.write(report_text)
    
    print(report_text)
    return report_text

def main():
    # パス設定
    base_dir = Path("/Users/takahashiryoutarou/Desktop/LLM実験/Physics/outputs")
    gpt52_dir = base_dir / "gpt-5.2_mechanics_output" / "mechanics_dataset"
    o3_dir = base_dir / "o3-mini_together_output" / "mechanics_dataset_textonly"
    output_dir = base_dir / "eda_gpt52_vs_o3"
    output_dir.mkdir(exist_ok=True)
    
    print("データを読み込んでいます...")
    # データ読み込み
    responses_gpt52 = load_jsonl(gpt52_dir / "response.jsonl")
    responses_o3 = load_jsonl(o3_dir / "response.jsonl")
    df_gpt52 = load_score_csv(gpt52_dir / "score.csv")
    df_o3 = load_score_csv(o3_dir / "score.csv")
    
    print(f"GPT-5.2: {len(responses_gpt52)}件, o3-mini: {len(responses_o3)}件")
    
    print("\n精度分布を分析しています...")
    stats_gpt52, stats_o3 = analyze_accuracy_distribution(df_gpt52, df_o3, output_dir)
    
    print("エラーケースを分析しています...")
    error_report = analyze_error_cases(responses_gpt52, responses_o3, output_dir)
    
    print("レスポンス特徴を分析しています...")
    response_stats = analyze_response_characteristics(responses_gpt52, responses_o3, output_dir)
    
    print("等価性チェック結果を分析しています...")
    equivalency_stats = analyze_equivalency_results(responses_gpt52, responses_o3, output_dir)
    
    print("トークン使用量を分析しています...")
    token_stats = analyze_token_usage(responses_gpt52, output_dir)
    
    print("\n総合レポートを生成しています...")
    generate_summary_report(stats_gpt52, stats_o3, error_report, response_stats,
                           equivalency_stats, token_stats, output_dir)
    
    print(f"\n分析完了！結果は {output_dir} に保存されました。")

if __name__ == "__main__":
    main()
