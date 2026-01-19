
# EDA Report: gpt-4o_mechanics_output vs gpt-4o_output

## 1. 全体精度比較

### gpt-4o_mechanics_output
- Overall Accuracy: 0.2768
- Variance: 0.1708
- Sympy Error Correct Ratio: 0.0000

### gpt-4o_output
- Overall Accuracy: 0.3332
- Variance: 0.1676
- Sympy Error Correct Ratio: 0.0635

### 精度差
- **精度差**: 0.0564 (20.36% 低い)

## 2. 統計サマリー

### gpt-4o_mechanics_output
- Mean Accuracy: 0.2768
- Median Accuracy: 0.0000
- Std Deviation: 0.4132
- Min Accuracy: 0.0000
- Max Accuracy: 1.0000

### gpt-4o_output
- Mean Accuracy: 0.3332
- Median Accuracy: 0.0000
- Std Deviation: 0.4094
- Min Accuracy: 0.0000
- Max Accuracy: 1.0000

## 3. エラー分析

### Sympyエラー
- gpt-4o_mechanics: 1032 エラー (383.64%)
- gpt-4o: 0 エラー (0.00%)

### LLMのみで正解
- gpt-4o_mechanics: 128 件
- gpt-4o: 79 件

## 4. レスポンス品質

### gpt-4o_mechanics_output
- Average Final Answers: 1.50
- Average Equivalency Results: 3.84
- Sympy Error Rate: 0.9888
- Average Response Length: 2730 characters

### gpt-4o_output
- Average Final Answers: 1.91
- Average Equivalency Results: 5.07
- Sympy Error Rate: 0.0000
- Average Response Length: 3920 characters

## 5. 個別エントリ分析

### 精度差が大きいエントリ（上位5件）

- **mechanics/2_11**: 0.0000 → 1.0000 (差: 1.0000)

- **mechanics/1_64**: 0.0000 → 1.0000 (差: 1.0000)

- **mechanics/3_40**: 0.0000 → 1.0000 (差: 1.0000)

- **mechanics/3_14**: 0.0000 → 1.0000 (差: 1.0000)

- **mechanics/1_82**: 0.0000 → 1.0000 (差: 1.0000)

## 6. 主な発見

1. **精度差**: gpt-4o_mechanics_outputはgpt-4o_outputより0.0564 (20.36%)低い

2. **Sympyエラー**: 両方のデータセットでSympyエラーが発生しているが、gpt-4o_outputの方がSympy Error Correct Ratioが高い

3. **精度分布**: 精度の分布に違いがある可能性がある

4. **個別エントリ**: 65個のエントリで精度差が0.3以上
