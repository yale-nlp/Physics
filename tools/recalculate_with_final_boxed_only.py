#!/usr/bin/env python3
"""
途中式の\boxed{}を除外し、最後の\boxed{}だけを抽出して精度を再計算するスクリプト
"""

import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Dict, List, Any, Tuple
import re
import sys
import os

# 親ディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import equation_equivilancy

# 日本語フォント設定
plt.rcParams['font.family'] = 'DejaVu Sans'
sns.set_style("whitegrid")
sns.set_palette("husl")

def extract_last_boxed_only(latex_response: str) -> List[str]:
    """
    最後の\boxed{}だけを抽出（途中式の\boxed{}は除外）
    """
    if not latex_response:
        return []
    
    # 全ての\boxed{}の位置を取得
    patterns = [
        (r'\\boxed\{((?:[^{}]|{(?:[^{}]|{.*?})*})*)\}', '\\boxed{'),
        (r'\\\[boxed\{((?:[^{}]|{(?:[^{}]|{.*?})*})*)\}\\\]', '\\[boxed{'),
        (r'\\\\\[boxed\{((?:[^{}]|{(?:[^{}]|{.*?})*})*)\}\\\\\]', '\\\\[boxed{'),
    ]
    
    all_matches = []
    for pattern, prefix in patterns:
        for match in re.finditer(pattern, latex_response, re.DOTALL):
            start_pos = match.start()
            end_pos = match.end()
            content = match.group(1).strip()
            if content:
                all_matches.append({
                    'start': start_pos,
                    'end': end_pos,
                    'content': content,
                    'full_match': match.group(0)
                })
    
    if not all_matches:
        return []
    
    # 最後の\boxed{}を取得（位置が最も後ろのもの）
    last_match = max(all_matches, key=lambda x: x['end'])
    
    # 最後の\boxed{}の内容を返す
    # リスト形式の場合は分割
    content = last_match['content']
    
    # リスト形式のチェック [a, b, c]
    list_match = re.match(r'\\\[(.*?)\\\]', content)
    if list_match:
        # リスト形式の場合
        items = [item.strip() for item in list_match.group(1).split(',')]
        return items
    else:
        # 単一の値の場合
        return [content]

def recalculate_accuracy(entry: Dict, use_final_boxed_only: bool = False) -> Tuple[float, int, int]:
    """
    精度を再計算
    use_final_boxed_only=Trueの場合、最後の\boxed{}だけを使用
    """
    entry_id = entry.get("id")
    solution = entry.get("solution", "")
    dataset_answers = entry.get("final_answers", [])  # これは元のデータセットの正解
    
    # 実際の正解はentryから取得する必要がある
    # response.jsonlには元のエントリの情報が含まれていない可能性がある
    # そのため、元のデータセットから正解を読み込む必要がある
    
    if use_final_boxed_only:
        # 最後の\boxed{}だけを抽出
        llm_final_answers = extract_last_boxed_only(solution)
    else:
        # 元のfinal_answersを使用（全ての\boxed{}）
        llm_final_answers = entry.get("final_answers", [])
    
    if not llm_final_answers:
        return 0.0, 0, 0
    
    # データセットの正解を取得
    # response.jsonlには含まれていない可能性があるので、
    # 元のデータセットから読み込む必要がある
    # ここでは、equivalency_resultsから正解を推測するか、
    # 元のデータセットファイルを読み込む必要がある
    
    # 暫定的に、equivalency_resultsから正解を推測
    equivalency_results = entry.get("equivalency_results", [])
    
    if not equivalency_results:
        return 0.0, 0, 0
    
    # equivalency_resultsから正解を抽出
    dataset_answers_from_results = []
    for eq_result in equivalency_results:
        # input_expressionsから正解を取得
        input_exprs = eq_result.get("input_expressions", {})
        expr2 = input_exprs.get("expr2", "")
        if expr2 and expr2 not in dataset_answers_from_results:
            dataset_answers_from_results.append(expr2)
    
    if not dataset_answers_from_results:
        return 0.0, 0, 0
    
    # 精度を計算
    correct_count = 0
    total_comparisons = len(llm_final_answers)
    
    for llm_answer in llm_final_answers:
        matched = False
        for dataset_answer in dataset_answers_from_results:
            equivalency_data = equation_equivilancy.is_equiv(llm_answer, dataset_answer, verbose=False)
            if equivalency_data.get("final_result") == True:
                correct_count += 1
                matched = True
                break
    
    accuracy = correct_count / total_comparisons if total_comparisons > 0 else 0.0
    
    return accuracy, correct_count, total_comparisons

def load_original_dataset(dataset_path: Path) -> Dict[str, List[str]]:
    """元のデータセットを読み込んで、各エントリの正解を取得"""
    answers_dict = {}
    with open(dataset_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                entry = json.loads(line)
                entry_id = entry.get("id", "")
                final_answers = entry.get("final_answers", [])
                answers_dict[entry_id] = final_answers
    return answers_dict

def recalculate_with_final_boxed_only(responses: List[Dict], 
                                     dataset_answers_dict: Dict[str, List[str]],
                                     model_name: str) -> Dict:
    """最後の\boxed{}だけを使用して精度を再計算"""
    results = []
    original_accuracies = []
    recalculated_accuracies = []
    
    total = len(responses)
    for idx, resp in enumerate(responses, 1):
        if idx % 50 == 0 or idx == total:
            print(f"  進捗: {idx}/{total} ({idx/total*100:.1f}%)", end='\r')
        entry_id = resp.get("id", "")
        solution = resp.get("solution", "")
        original_final_answers = resp.get("final_answers", [])
        original_accuracy = resp.get("accuracy", 0)
        
        # 元のデータセットから正解を取得
        dataset_answers = dataset_answers_dict.get(entry_id, [])
        
        if not dataset_answers:
            # dataset_answers_dictにない場合は、equivalency_resultsから推測
            equivalency_results = resp.get("equivalency_results", [])
            for eq_result in equivalency_results:
                input_exprs = eq_result.get("input_expressions", {})
                expr2 = input_exprs.get("expr2", "")
                if expr2 and expr2 not in dataset_answers:
                    dataset_answers.append(expr2)
        
        # 最後の\boxed{}だけを抽出
        final_boxed_only_answers = extract_last_boxed_only(solution)
        
        # 精度を再計算
        if final_boxed_only_answers and dataset_answers:
            correct_count = 0
            total_comparisons = len(final_boxed_only_answers)
            
            # any-match方式（1つでも当たれば1）
            matched = False
            for llm_answer in final_boxed_only_answers:
                if matched:
                    break
                for dataset_answer in dataset_answers:
                    equivalency_data = equation_equivilancy.is_equiv(llm_answer, dataset_answer, verbose=False)
                    if equivalency_data.get("final_result") == True:
                        correct_count = 1
                        matched = True
                        break
            
            # 元の方式（正解数 / 抽出解数）も計算
            correct_count_original = 0
            for llm_answer in final_boxed_only_answers:
                for dataset_answer in dataset_answers:
                    equivalency_data = equation_equivilancy.is_equiv(llm_answer, dataset_answer, verbose=False)
                    if equivalency_data.get("final_result") == True:
                        correct_count_original += 1
                        break
            
            recalculated_accuracy = correct_count_original / total_comparisons if total_comparisons > 0 else 0.0
        else:
            recalculated_accuracy = 0.0
        
        results.append({
            'id': entry_id,
            'original_final_answers_count': len(original_final_answers),
            'final_boxed_only_count': len(final_boxed_only_answers),
            'original_accuracy': original_accuracy,
            'recalculated_accuracy': recalculated_accuracy,
            'accuracy_diff': recalculated_accuracy - original_accuracy
        })
        
        original_accuracies.append(original_accuracy)
        recalculated_accuracies.append(recalculated_accuracy)
    
    return {
        'model_name': model_name,
        'results': results,
        'original_mean_accuracy': sum(original_accuracies) / len(original_accuracies) if original_accuracies else 0,
        'recalculated_mean_accuracy': sum(recalculated_accuracies) / len(recalculated_accuracies) if recalculated_accuracies else 0,
        'accuracy_improvement': sum(recalculated_accuracies) / len(recalculated_accuracies) - sum(original_accuracies) / len(original_accuracies) if original_accuracies and recalculated_accuracies else 0
    }

def visualize_recalculation_results(all_results: Dict[str, Dict], output_dir: Path):
    """再計算結果の可視化"""
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    model_names = list(all_results.keys())
    colors = sns.color_palette("husl", len(model_names))
    
    # 1. 元の精度 vs 再計算後の精度
    original_accs = [all_results[name]['original_mean_accuracy'] for name in model_names]
    recalculated_accs = [all_results[name]['recalculated_mean_accuracy'] for name in model_names]
    
    x = np.arange(len(model_names))
    width = 0.35
    
    axes[0, 0].bar(x - width/2, original_accs, width, label='Original (All Boxed)', alpha=0.7)
    axes[0, 0].bar(x + width/2, recalculated_accs, width, label='Recalculated (Final Boxed Only)', alpha=0.7)
    axes[0, 0].set_xticks(x)
    axes[0, 0].set_xticklabels(model_names, rotation=45, ha='right')
    axes[0, 0].set_ylabel('Mean Accuracy')
    axes[0, 0].set_title('Accuracy Comparison: Original vs Recalculated')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3, axis='y')
    
    # 値を表示
    for i, (orig, recalc) in enumerate(zip(original_accs, recalculated_accs)):
        axes[0, 0].text(i - width/2, orig + 0.01, f'{orig:.3f}', ha='center', va='bottom', fontsize=8)
        axes[0, 0].text(i + width/2, recalc + 0.01, f'{recalc:.3f}', ha='center', va='bottom', fontsize=8)
    
    # 2. 精度改善量
    improvements = [all_results[name]['accuracy_improvement'] for name in model_names]
    colors_improvement = ['green' if imp > 0 else 'red' for imp in improvements]
    axes[0, 1].bar(range(len(model_names)), improvements, color=colors_improvement, alpha=0.7)
    axes[0, 1].set_xticks(range(len(model_names)))
    axes[0, 1].set_xticklabels(model_names, rotation=45, ha='right')
    axes[0, 1].set_ylabel('Accuracy Improvement')
    axes[0, 1].set_title('Accuracy Improvement (Final Boxed Only)')
    axes[0, 1].axhline(y=0, color='black', linestyle='--', linewidth=1)
    axes[0, 1].grid(True, alpha=0.3, axis='y')
    for i, imp in enumerate(improvements):
        axes[0, 1].text(i, imp + (0.01 if imp > 0 else -0.01), f'{imp:+.3f}', 
                       ha='center', va='bottom' if imp > 0 else 'top', fontsize=8)
    
    # 3. 精度差の分布
    for i, name in enumerate(model_names):
        results = all_results[name]['results']
        accuracy_diffs = [r['accuracy_diff'] for r in results]
        axes[1, 0].hist(accuracy_diffs, bins=30, alpha=0.6, label=name, edgecolor='black')
    axes[1, 0].set_xlabel('Accuracy Difference (Recalculated - Original)')
    axes[1, 0].set_ylabel('Frequency')
    axes[1, 0].set_title('Accuracy Difference Distribution')
    axes[1, 0].axvline(x=0, color='red', linestyle='--', linewidth=2)
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)
    
    # 4. 統計サマリー
    stats_text = "Statistics Summary:\n\n"
    for name in model_names:
        results = all_results[name]['results']
        stats_text += f"{name}:\n"
        stats_text += f"  Original Mean: {all_results[name]['original_mean_accuracy']:.4f}\n"
        stats_text += f"  Recalculated Mean: {all_results[name]['recalculated_mean_accuracy']:.4f}\n"
        stats_text += f"  Improvement: {all_results[name]['accuracy_improvement']:+.4f}\n"
        stats_text += f"  Improved Cases: {sum(1 for r in results if r['accuracy_diff'] > 0)}\n"
        stats_text += f"  Worsened Cases: {sum(1 for r in results if r['accuracy_diff'] < 0)}\n"
        stats_text += f"  No Change Cases: {sum(1 for r in results if r['accuracy_diff'] == 0)}\n\n"
    
    axes[1, 1].text(0.1, 0.5, stats_text, fontsize=9, verticalalignment='center',
                    family='monospace', transform=axes[1, 1].transAxes)
    axes[1, 1].axis('off')
    axes[1, 1].set_title('Statistics Summary')
    
    plt.tight_layout()
    plt.savefig(output_dir / 'recalculation_results.png', dpi=300, bbox_inches='tight')
    print(f"Saved: {output_dir / 'recalculation_results.png'}")
    plt.close()

def generate_recalculation_report(all_results: Dict[str, Dict], output_dir: Path):
    """再計算結果のレポートを生成"""
    report = """
# 最後の\\boxed{}のみを使用した精度再計算レポート

## 1. 精度比較

"""
    
    for name in all_results.keys():
        result = all_results[name]
        improvement_pct = result['accuracy_improvement'] / result['original_mean_accuracy'] * 100 if result['original_mean_accuracy'] > 0 else 0
        report += f"""
### {name}
- **元の精度（全ての\\boxed{{}}）**: {result['original_mean_accuracy']:.4f}
- **再計算後の精度（最後の\\boxed{{}}のみ）**: {result['recalculated_mean_accuracy']:.4f}
- **精度改善**: {result['accuracy_improvement']:+.4f} ({improvement_pct:+.2f}%)
"""
    
    report += "\n## 2. 詳細統計\n\n"
    
    for name in all_results.keys():
        results = all_results[name]['results']
        improved = sum(1 for r in results if r['accuracy_diff'] > 0)
        worsened = sum(1 for r in results if r['accuracy_diff'] < 0)
        no_change = sum(1 for r in results if r['accuracy_diff'] == 0)
        
        report += f"""
### {name}
- 改善したケース: {improved}件 ({improved/len(results)*100:.2f}%)
- 悪化したケース: {worsened}件 ({worsened/len(results)*100:.2f}%)
- 変化なし: {no_change}件 ({no_change/len(results)*100:.2f}%)
"""
    
    report += "\n## 3. 主な発見\n\n"
    
    # 改善率ランキング
    improvements = {name: all_results[name]['accuracy_improvement'] for name in all_results.keys()}
    sorted_models = sorted(improvements.items(), key=lambda x: x[1], reverse=True)
    
    report += "### 精度改善ランキング\n"
    for rank, (name, imp) in enumerate(sorted_models, 1):
        report += f"{rank}. {name}: {imp:+.4f}\n"
    
    report += "\n### 結論\n\n"
    report += "途中式の\\boxed{{}}を除外し、最後の\\boxed{{}}だけを使用することで、\n"
    report += "GPT-5.2などのモデルで精度が改善する可能性があります。\n"
    report += "これは、途中式で\\boxed{{}}を使うことで抽出解数が増え、\n"
    report += "採点指標（accuracy = 正解数 / 抽出解数）により精度が下がっていたためです。\n"
    
    # CSVとして保存
    all_data = []
    for name in all_results.keys():
        for r in all_results[name]['results']:
            all_data.append({
                'model': name,
                'entry_id': r['id'],
                'original_final_answers_count': r['original_final_answers_count'],
                'final_boxed_only_count': r['final_boxed_only_count'],
                'original_accuracy': r['original_accuracy'],
                'recalculated_accuracy': r['recalculated_accuracy'],
                'accuracy_diff': r['accuracy_diff']
            })
    
    df = pd.DataFrame(all_data)
    df.to_csv(output_dir / 'recalculation_comparison.csv', index=False)
    print(f"Saved: {output_dir / 'recalculation_comparison.csv'}")
    
    with open(output_dir / 'recalculation_report.md', 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"Saved: {output_dir / 'recalculation_report.md'}")
    print("\n" + "="*80)
    print(report)
    print("="*80)

def main():
    base_dir = Path("/Users/takahashiryoutarou/Desktop/LLM実験/Physics/outputs")
    dataset_path = Path("/Users/takahashiryoutarou/Desktop/LLM実験/Physics/PHYSICS/mechanics_dataset.jsonl")
    
    # 元のデータセットを読み込む
    print("元のデータセットを読み込んでいます...")
    dataset_answers_dict = load_original_dataset(dataset_path)
    print(f"✓ {len(dataset_answers_dict)}件のエントリを読み込み")
    
    # 最近追加されたoutputの定義
    output_configs = [
        ("gemini-3.0-pro", "gemini-3.0-pro_output/mechanics_dataset/response.jsonl"),
        ("gpt-5.2", "gpt-5.2_mechanics_output/mechanics_dataset/response.jsonl"),
        ("gpt-4o-rerun", "gpt-4o_mechanics_output_rerun/mechanics_dataset/response.jsonl"),
    ]
    
    print("\nデータを読み込んでいます...")
    all_responses = {}
    for name, file_path in output_configs:
        try:
            responses = []
            with open(base_dir / file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        responses.append(json.loads(line))
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
    
    print("\n精度を再計算しています...")
    all_results = {}
    
    for name, responses in all_responses.items():
        print(f"\n{name}を処理中... ({len(responses)}件)")
        result = recalculate_with_final_boxed_only(responses, dataset_answers_dict, name)
        all_results[name] = result
        print(f"  元の精度: {result['original_mean_accuracy']:.4f}")
        print(f"  再計算後の精度: {result['recalculated_mean_accuracy']:.4f}")
        print(f"  改善: {result['accuracy_improvement']:+.4f}")
    
    print("\n可視化しています...")
    visualize_recalculation_results(all_results, output_dir)
    
    print("\nレポートを生成しています...")
    generate_recalculation_report(all_results, output_dir)
    
    print(f"\n再計算完了！結果は {output_dir} に保存されました。")

if __name__ == "__main__":
    import numpy as np
    main()
