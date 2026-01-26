# Reasoningパラメータ有無による比較手順

## 概要

GPT-5.2のResponses APIで`reasoning`パラメータを追加した場合と追加しない場合の評価結果を比較します。

## ファイル構成

- `evaluate_mechanics_gpt5_2.py`: reasoningパラメータあり版（`reasoning: {"effort": "high"}`）
- `evaluate_mechanics_gpt5_2_no_reasoning.py`: reasoningパラメータなし版
- `compare_reasoning_results.py`: 2つの結果を比較するスクリプト

## 実行手順

### 1. reasoningパラメータあり版の実行（既に実行中）

```bash
cd api_evaluation
python evaluate_mechanics_gpt5_2.py
```

出力先: `../outputs/gpt-5.2_mechanics_output/mechanics_dataset/`

### 2. reasoningパラメータなし版の実行

```bash
cd api_evaluation
python evaluate_mechanics_gpt5_2_no_reasoning.py
```

出力先: `../outputs/gpt-5.2_mechanics_output_no_reasoning/mechanics_dataset/`

### 3. 結果の比較

両方の評価が完了したら、比較スクリプトを実行します：

```bash
cd api_evaluation
python compare_reasoning_results.py \
  ../outputs/gpt-5.2_mechanics_output_no_reasoning/mechanics_dataset \
  ../outputs/gpt-5.2_mechanics_output/mechanics_dataset \
  ../outputs/reasoning_comparison
```

## 比較項目

比較スクリプトは以下の項目を分析します：

1. **精度比較**
   - 平均精度（reasoningなし vs reasoningあり）
   - 精度の差分分布
   - 改善/悪化/変化なしの問題数

2. **トークン使用量比較**
   - Prompt Tokens
   - Completion Tokens
   - Total Tokens
   - 問題あたりの平均トークン数

3. **可視化**
   - Accuracy比較散布図
   - Accuracy差分の分布ヒストグラム
   - トークン使用量比較バーチャート
   - 結果変化の内訳（円グラフ）

## 出力ファイル

比較結果は以下のファイルとして保存されます：

- `comparison.csv`: 各問題の詳細比較データ
- `summary.csv`: 統計サマリー
- `comparison_plots.png`: 可視化プロット
- `comparison_report.md`: マークダウンレポート

## 現在の状況

### reasoningパラメータあり版（実行中）

- 処理済み: 96問/221問（進行中）
- 現在の精度: 34.38%（進行中）
- 成功: 88問/365問（チェックポイント含む）
- 平均精度: 61.36%（成功した問題のみ）
- 平均トークン数: 3,788トークン/問題

### reasoningパラメータなし版

- 未実行（実行が必要）

## 注意事項

1. 両方の評価が完了してから比較スクリプトを実行してください
2. 評価には時間がかかります（221問 × 約2-3時間）
3. APIコストに注意してください（reasoningあり版はより多くのトークンを使用する可能性があります）
