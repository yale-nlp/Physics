
# Boxed形式の回答抽出エラー分析レポート

## 1. エラー統計


### gemini-3.0-pro
- 総エントリ数: 221
- 空のfinal_answers: 2 (0.90%)
- solutionあり（空のfinal_answers）: 0
- solutionにboxed形式あり: 0
- solutionなし: 2
- 平均solution長（空のfinal_answers）: 0 文字

### gpt-5.2
- 総エントリ数: 221
- 空のfinal_answers: 0 (0.00%)
- solutionあり（空のfinal_answers）: 0
- solutionにboxed形式あり: 0
- solutionなし: 0
- 平均solution長（空のfinal_answers）: 0 文字

### gpt-4o-rerun
- 総エントリ数: 221
- 空のfinal_answers: 126 (57.01%)
- solutionあり（空のfinal_answers）: 0
- solutionにboxed形式あり: 0
- solutionなし: 126
- 平均solution長（空のfinal_answers）: 0 文字

## 2. エラーケースのサンプル

### gemini-3.0-pro

1. Entry ID: mechanics/3_4
   - Solutionあり: False
   - Solution長: 0 文字
   - Boxed形式あり: False

2. Entry ID: mechanics/2_14
   - Solutionあり: False
   - Solution長: 0 文字
   - Boxed形式あり: False

### gpt-5.2

### gpt-4o-rerun

1. Entry ID: mechanics/1_43
   - Solutionあり: False
   - Solution長: 0 文字
   - Boxed形式あり: False

2. Entry ID: mechanics/1_88
   - Solutionあり: False
   - Solution長: 0 文字
   - Boxed形式あり: False

3. Entry ID: mechanics/1_72
   - Solutionあり: False
   - Solution長: 0 文字
   - Boxed形式あり: False

4. Entry ID: mechanics/1_28
   - Solutionあり: False
   - Solution長: 0 文字
   - Boxed形式あり: False

5. Entry ID: mechanics/1_17
   - Solutionあり: False
   - Solution長: 0 文字
   - Boxed形式あり: False

6. Entry ID: mechanics/2_30
   - Solutionあり: False
   - Solution長: 0 文字
   - Boxed形式あり: False

7. Entry ID: mechanics/1_10
   - Solutionあり: False
   - Solution長: 0 文字
   - Boxed形式あり: False

8. Entry ID: mechanics/1_87
   - Solutionあり: False
   - Solution長: 0 文字
   - Boxed形式あり: False

9. Entry ID: mechanics/1_80
   - Solutionあり: False
   - Solution長: 0 文字
   - Boxed形式あり: False

10. Entry ID: mechanics/1_42
   - Solutionあり: False
   - Solution長: 0 文字
   - Boxed形式あり: False


## 3. 主な発見

1. **エラー率ランキング**:
   1. gpt-4o-rerun: 57.01%
   2. gemini-3.0-pro: 0.90%
   3. gpt-5.2: 0.00%

2. **Boxed形式が含まれているのに抽出できなかったケース**:

3. **Solutionがないケース**:
   - gemini-3.0-pro: 2件（LLMが回答を生成できなかった）
   - gpt-4o-rerun: 126件（LLMが回答を生成できなかった）

詳細は生成されたグラフとサンプルを参照してください。
