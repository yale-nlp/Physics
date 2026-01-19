#!/usr/bin/env python3
"""
GPT-5.2のみ：途中式の\boxed{}を除外し、最後の\boxed{}だけを抽出して精度を再計算するスクリプト
"""

import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Dict, List, Any
import re
import sys
import os
from tqdm import tqdm

# 親ディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import equation_equivilancy

# 日本語フォント設定
plt.rcParams['font.family'] = 'DejaVu Sans'
sns.set_style("whitegrid")

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

def recalculate_accuracy(responses: List[Dict], 
                         dataset_answers_dict: Dict[str, List[str]],
                         model_name: str) -> Dict:
    """モデルの精度を再計算（既存のequivalency_resultsを活用）"""
    results = []
    original_accuracies = []
    recalculated_accuracies = []
    
    print(f"  221件のエントリを処理中...")
    for idx, resp in enumerate(tqdm(responses, desc="  進捗"), 1):
        entry_id = resp.get("id", "")
        solution = resp.get("solution", "")
        original_final_answers = resp.get("final_answers", [])
        original_accuracy = resp.get("accuracy", 0)
        equivalency_results = resp.get("equivalency_results", [])
        
        # 最後の\boxed{}だけを抽出
        final_boxed_only_answers = extract_last_boxed_only(solution)
        
        # 既存のequivalency_resultsを活用して精度を再計算
        # 最後の\boxed{}の回答が、元のfinal_answersのどれかに一致するかを確認
        # 一致するものに対応するequivalency_resultsを使って精度を計算
        
        if final_boxed_only_answers and equivalency_results and original_final_answers:
            # 最後の\boxed{}の回答が、元のfinal_answersのどれかに一致するかを確認
            # 通常、最後の\boxed{}は元のfinal_answersの最後のものと一致する可能性が高い
            # または、複数の\boxed{}がある場合は、最後のものだけを抽出
            
            # 最後の\boxed{}の回答に対応するequivalency_resultsを探す
            matched_results = []
            
            # 最後の\boxed{}の回答（通常は1つ）
            last_boxed_answer = final_boxed_only_answers[-1] if final_boxed_only_answers else None
            
            if last_boxed_answer:
                # 元のfinal_answersから一致するものを探す
                for orig_answer in original_final_answers:
                    # 文字列として一致するか確認
                    if last_boxed_answer == orig_answer or last_boxed_answer.strip() == orig_answer.strip():
                        # この回答に対応するequivalency_resultsを全て探す
                        for eq_result in equivalency_results:
                            input_exprs = eq_result.get("input_expressions", {})
                            expr1 = input_exprs.get("expr1", "")
                            if expr1 == orig_answer or expr1.strip() == orig_answer.strip():
                                matched_results.append(eq_result)
                        break
                
                # マッチした結果から精度を計算
                if matched_results:
                    # any-match方式：1つでも正解があれば1
                    correct_count = 1 if any(eq_result.get("final_result") == True for eq_result in matched_results) else 0
                    total_comparisons = 1  # 最後の\boxed{}は1つなので
                    recalculated_accuracy = correct_count / total_comparisons if total_comparisons > 0 else 0.0
                else:
                    # マッチしない場合は0
                    recalculated_accuracy = 0.0
            else:
                recalculated_accuracy = 0.0
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

def visualize_results(result: Dict, output_dir: Path):
    """結果の可視化"""
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    model_name = result['model_name']
    results = result['results']
    
    # 1. 元の精度 vs 再計算後の精度の散布図
    original_accs = [r['original_accuracy'] for r in results]
    recalculated_accs = [r['recalculated_accuracy'] for r in results]
    
    axes[0, 0].scatter(original_accs, recalculated_accs, alpha=0.6, s=30)
    axes[0, 0].plot([0, 1], [0, 1], 'r--', linewidth=2, label='y=x')
    axes[0, 0].set_xlabel('Original Accuracy (All Boxed)')
    axes[0, 0].set_ylabel('Recalculated Accuracy (Final Boxed Only)')
    axes[0, 0].set_title('Accuracy Comparison: Original vs Recalculated')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)
    
    # 2. 精度改善量の分布
    accuracy_diffs = [r['accuracy_diff'] for r in results]
    axes[0, 1].hist(accuracy_diffs, bins=30, alpha=0.7, color='green', edgecolor='black')
    axes[0, 1].axvline(x=0, color='red', linestyle='--', linewidth=2)
    axes[0, 1].set_xlabel('Accuracy Difference (Recalculated - Original)')
    axes[0, 1].set_ylabel('Frequency')
    axes[0, 1].set_title('Accuracy Improvement Distribution')
    axes[0, 1].grid(True, alpha=0.3)
    
    # 3. Final Answers数の比較
    original_counts = [r['original_final_answers_count'] for r in results]
    final_boxed_counts = [r['final_boxed_only_count'] for r in results]
    
    axes[1, 0].hist(original_counts, bins=range(0, max(max(original_counts), max(final_boxed_counts)) + 2), 
                   alpha=0.6, label='Original (All Boxed)', edgecolor='black', align='left')
    axes[1, 0].hist(final_boxed_counts, bins=range(0, max(max(original_counts), max(final_boxed_counts)) + 2), 
                   alpha=0.6, label='Recalculated (Final Boxed Only)', edgecolor='black', align='left')
    axes[1, 0].set_xlabel('Number of Final Answers')
    axes[1, 0].set_ylabel('Frequency')
    axes[1, 0].set_title('Final Answers Count Comparison')
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)
    
    # 4. 統計サマリー
    improved = sum(1 for r in results if r['accuracy_diff'] > 0)
    worsened = sum(1 for r in results if r['accuracy_diff'] < 0)
    no_change = sum(1 for r in results if r['accuracy_diff'] == 0)
    
    stats_text = f"""Statistics Summary:

Original Mean Accuracy: {result['original_mean_accuracy']:.4f}
Recalculated Mean Accuracy: {result['recalculated_mean_accuracy']:.4f}
Accuracy Improvement: {result['accuracy_improvement']:+.4f}

Improved Cases: {improved} ({improved/len(results)*100:.1f}%)
Worsened Cases: {worsened} ({worsened/len(results)*100:.1f}%)
No Change Cases: {no_change} ({no_change/len(results)*100:.1f}%)

Avg Original Final Answers: {sum(original_counts)/len(original_counts):.2f}
Avg Final Boxed Only Count: {sum(final_boxed_counts)/len(final_boxed_counts):.2f}"""
    
    axes[1, 1].text(0.1, 0.5, stats_text, fontsize=10, verticalalignment='center',
                    family='monospace', transform=axes[1, 1].transAxes)
    axes[1, 1].axis('off')
    axes[1, 1].set_title('Statistics Summary')
    
    plt.tight_layout()
    filename = f'{model_name.replace("-", "_").replace(".", "_")}_recalculation_results.png'
    plt.savefig(output_dir / filename, dpi=300, bbox_inches='tight')
    print(f"Saved: {output_dir / filename}")
    plt.close()

def generate_report(result: Dict, output_dir: Path):
    """レポートを生成"""
    model_name = result['model_name']
    results = result['results']
    improved = sum(1 for r in results if r['accuracy_diff'] > 0)
    worsened = sum(1 for r in results if r['accuracy_diff'] < 0)
    no_change = sum(1 for r in results if r['accuracy_diff'] == 0)
    
    improvement_pct = result['accuracy_improvement'] / result['original_mean_accuracy'] * 100 if result['original_mean_accuracy'] > 0 else 0
    
    report = f"""
# {model_name}: 最後の\\boxed{{}}のみを使用した精度再計算レポート

## 1. 精度比較

- **元の精度（全ての\\boxed{{}}）**: {result['original_mean_accuracy']:.4f}
- **再計算後の精度（最後の\\boxed{{}}のみ）**: {result['recalculated_mean_accuracy']:.4f}
- **精度改善**: {result['accuracy_improvement']:+.4f} ({improvement_pct:+.2f}%)

## 2. 詳細統計

- 改善したケース: {improved}件 ({improved/len(results)*100:.2f}%)
- 悪化したケース: {worsened}件 ({worsened/len(results)*100:.2f}%)
- 変化なし: {no_change}件 ({no_change/len(results)*100:.2f}%)

## 3. 主な発見

途中式の\\boxed{{}}を除外し、最後の\\boxed{{}}だけを使用することで、
{model_name}の精度が{result['accuracy_improvement']:+.4f} ({improvement_pct:+.2f}%)改善しました。

これは、途中式で\\boxed{{}}を使うことで抽出解数が増え、
採点指標（accuracy = 正解数 / 抽出解数）により精度が下がっていたためです。
"""
    
    # CSVとして保存
    df = pd.DataFrame(results)
    csv_filename = f'{model_name.replace("-", "_").replace(".", "_")}_recalculation_comparison.csv'
    df.to_csv(output_dir / csv_filename, index=False)
    print(f"Saved: {output_dir / csv_filename}")
    
    report_filename = f'{model_name.replace("-", "_").replace(".", "_")}_recalculation_report.md'
    with open(output_dir / report_filename, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"Saved: {output_dir / report_filename}")
    print("\n" + "="*80)
    print(report)
    print("="*80)

def main():
    base_dir = Path("/Users/takahashiryoutarou/Desktop/LLM実験/Physics/outputs")
    dataset_path = Path("/Users/takahashiryoutarou/Desktop/LLM実験/Physics/PHYSICS/mechanics_dataset.jsonl")
    
    # 処理するモデルの設定
    models = [
        ("gpt-5.2", "gpt-5.2_mechanics_output/mechanics_dataset/response.jsonl"),
        ("gemini-3.0-pro", "gemini-3.0-pro_output/mechanics_dataset/response.jsonl"),
    ]
    
    # 元のデータセットを読み込む
    print("元のデータセットを読み込んでいます...")
    dataset_answers_dict = load_original_dataset(dataset_path)
    print(f"✓ {len(dataset_answers_dict)}件のエントリを読み込み")
    
    # 出力ディレクトリ
    output_dir = base_dir / "recent_outputs_comparison"
    output_dir.mkdir(exist_ok=True)
    
    # 各モデルを処理
    for model_name, response_path_rel in models:
        print(f"\n{'='*60}")
        print(f"{model_name}を処理中...")
        print(f"{'='*60}")
        
        # response.jsonlを読み込む
        print(f"\n{model_name}のデータを読み込んでいます...")
        responses = []
        response_path = base_dir / response_path_rel
        try:
            with open(response_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        responses.append(json.loads(line))
            print(f"✓ {len(responses)}件のエントリを読み込み")
        except FileNotFoundError:
            print(f"✗ ファイルが見つかりません: {response_path}")
            continue
        
        print("\n精度を再計算しています...")
        result = recalculate_accuracy(responses, dataset_answers_dict, model_name)
        
        print(f"\n結果:")
        print(f"  元の精度: {result['original_mean_accuracy']:.4f}")
        print(f"  再計算後の精度: {result['recalculated_mean_accuracy']:.4f}")
        print(f"  改善: {result['accuracy_improvement']:+.4f}")
        
        print("\n可視化しています...")
        visualize_results(result, output_dir)
        
        print("\nレポートを生成しています...")
        generate_report(result, output_dir)
        
        print(f"\n{model_name}の再計算完了！")
    
    print(f"\n{'='*60}")
    print(f"全ての処理が完了しました！結果は {output_dir} に保存されました。")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
