
# EDA Report: gpt-4o_mechanics_output/mechanics_dataset_deduplicated vs gpt-4o_output/mechanics_dataset

## 1. 全体精度比較

### gpt-4o_mechanics_output/mechanics_dataset_deduplicated
- Overall Accuracy: 0.2829
- Variance: 0.1739
- Sympy Error Correct Ratio: 0.0000

### gpt-4o_output/mechanics_dataset
- Overall Accuracy: 0.3332
- Variance: 0.1676
- Sympy Error Correct Ratio: 0.0635

### 精度差
- **精度差**: 0.0503 (17.79% 高い)

## 2. 統計サマリー

### gpt-4o_mechanics_output/mechanics_dataset_deduplicated
- Mean Accuracy: 0.2829
- Median Accuracy: 0.0000
- Std Deviation: 0.4170
- Min Accuracy: 0.0000
- Max Accuracy: 1.0000
- Total Entries: 221

### gpt-4o_output/mechanics_dataset
- Mean Accuracy: 0.3332
- Median Accuracy: 0.0000
- Std Deviation: 0.4094
- Min Accuracy: 0.0000
- Max Accuracy: 1.0000
- Total Entries: 221

## 3. エラー分析

### Sympyエラー
- gpt-4o_mechanics_deduplicated: 862 エラー (390.05%)
- gpt-4o: 107 エラー (48.42%)

### Antlr4エラー（LaTeXパースエラー）
- gpt-4o_mechanics_deduplicated: 862 エラー (390.05%)
- gpt-4o: 0 エラー (0.00%)

### LLMのみで正解
- gpt-4o_mechanics_deduplicated: 102 件
- gpt-4o: 79 件

## 4. レスポンス品質

### gpt-4o_mechanics_output/mechanics_dataset_deduplicated
- Average Final Answers: 1.50
- Average Equivalency Results: 3.90
- Sympy Error Rate: 0.9910
- Antlr4 Error Rate: 0.9910
- Average Response Length: 2742 characters

### gpt-4o_output/mechanics_dataset
- Average Final Answers: 1.91
- Average Equivalency Results: 5.07
- Sympy Error Rate: 0.1810
- Antlr4 Error Rate: 0.0000
- Average Response Length: 3920 characters

## 5. 個別エントリ分析

### 精度差が大きいエントリ（上位5件）

- **mechanics/2_7**: 0.0000 → 1.0000 (差: 1.0000)

- **mechanics/1_8**: 0.0000 → 1.0000 (差: 1.0000)

- **mechanics/1_82**: 0.0000 → 1.0000 (差: 1.0000)

- **mechanics/2_11**: 0.0000 → 1.0000 (差: 1.0000)

- **mechanics/2_15**: 0.0000 → 1.0000 (差: 1.0000)

### エントリの重複状況
- 両方に存在するエントリ: 61個
- deduplicatedのみに存在: 119個
- gpt-4oのみに存在: 145個

## 6. 主な発見

1. **精度差**: gpt-4o_mechanics_deduplicatedはgpt-4o_outputより0.0503 (17.79%)高い

2. **Antlr4エラー**: gpt-4o_mechanics_deduplicatedでAntlr4エラーが発生している

3. **データセットサイズ**: deduplicated版は221エントリ、gpt-4oは221エントリ

4. **個別エントリ**: 65個のエントリで精度差が0.3以上
