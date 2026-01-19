
# 最近追加されたOutput比較レポート

## 1. 全体精度比較


### gemini-3.0-pro
- Overall Accuracy: 0.3983
- Variance: 0.2205
- Sympy Error Correct Ratio: 0.0000

### gpt-5.2
- Overall Accuracy: 0.4643
- Variance: 0.2190
- Sympy Error Correct Ratio: 0.0000
- Total Tokens: 272929
- Avg Tokens / Problem: 1234.97

### gpt-4o-rerun
- Overall Accuracy: 0.1020
- Variance: 0.0794
- Sympy Error Correct Ratio: 0.0000
- Total Tokens: 119287
- Avg Tokens / Problem: 539.76

### 精度ランキング
1. gpt-5.2: 0.4643
2. gemini-3.0-pro: 0.3983
3. gpt-4o-rerun: 0.1020

## 2. 統計サマリー


### gemini-3.0-pro
- Mean Accuracy: 0.3983
- Median Accuracy: 0.0000
- Std Deviation: 0.4696
- Min Accuracy: 0.0000
- Max Accuracy: 1.0000
- Total Entries: 221

### gpt-5.2
- Mean Accuracy: 0.4643
- Median Accuracy: 0.3333
- Std Deviation: 0.4679
- Min Accuracy: 0.0000
- Max Accuracy: 1.0000
- Total Entries: 221

### gpt-4o-rerun
- Mean Accuracy: 0.1020
- Median Accuracy: 0.0000
- Std Deviation: 0.2818
- Min Accuracy: 0.0000
- Max Accuracy: 1.0000
- Total Entries: 221

## 3. エラー分析


### gemini-3.0-pro
- Sympy Errors: 168 (76.02%)
- Antlr4 Errors: 0 (0.00%)
- LLM Only Correct: 48 件

### gpt-5.2
- Sympy Errors: 316 (142.99%)
- Antlr4 Errors: 0 (0.00%)
- LLM Only Correct: 121 件

### gpt-4o-rerun
- Sympy Errors: 15 (6.79%)
- Antlr4 Errors: 0 (0.00%)
- LLM Only Correct: 9 件

## 4. レスポンス品質


### gemini-3.0-pro
- Average Final Answers: 1.31
- Average Equivalency Results: 3.28
- Sympy Error Rate: 0.2805
- Antlr4 Error Rate: 0.0000
- Average Response Length: 4545 characters

### gpt-5.2
- Average Final Answers: 1.72
- Average Equivalency Results: 3.95
- Sympy Error Rate: 0.4977
- Antlr4 Error Rate: 0.0000
- Average Response Length: 2445 characters

### gpt-4o-rerun
- Average Final Answers: 0.65
- Average Equivalency Results: 1.67
- Sympy Error Rate: 0.0543
- Antlr4 Error Rate: 0.0000
- Average Response Length: 2720 characters

## 5. 主な発見

1. **最高精度**: gpt-5.2 (0.4643)
2. **精度差**: 0.3623 (355.36%)
3. **Antlr4エラー**: 全てのモデルでAntlr4エラーなし

詳細は生成されたグラフとCSVファイルを参照してください。
