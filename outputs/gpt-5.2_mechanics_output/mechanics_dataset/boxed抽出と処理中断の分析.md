# boxed抽出と処理中断の分析結果

## boxed抽出エラーの確認結果

### 分析結果

**boxed抽出エラーはありませんでした。**

- `solution≠null かつ final_answers=[]`: **0件**
- `solution≠null かつ final_answers≠[]`: **103件**

つまり、API呼び出しが成功して`solution`が取得できた場合、すべて`\boxed{}`形式の抽出も成功しています。

### 結論

**boxed抽出の処理は正常に動作しています。** エラーの原因は、API呼び出し自体の失敗（`solution=null`）であり、boxed抽出の問題ではありません。

## 処理中断による重複エントリの問題

### 問題の概要

PCを閉じたことによる処理中断により、**重複エントリ**が発生しています。

### 統計情報

- **総エントリ数**: 389件（重複含む）
- **ユニークなID数**: 221件（全問題数）
- **重複ID数**: 144件

### 重複の原因

チェックポイント保存機能により、処理が中断されて再実行された際に、同じ問題IDが複数回記録されています。

**例**:
```
ID: mechanics/1_9 - 3回出現
  エントリ1 (line 3): solution=null, final_answers=空
  エントリ2 (line 224): solution=あり, final_answers=1個  ← 最新（正しい）
  エントリ3 (line 248): solution=あり, final_answers=1個  ← 最新（正しい）
```

### 影響

1. **統計の不正確さ**: 重複エントリにより、統計情報が不正確になっている可能性
2. **最新エントリの使用**: 通常、最新のエントリ（最後に記録されたもの）が正しい結果

## 推奨される対応

### 1. 重複エントリの除去

最新のエントリのみを残すスクリプトを作成することを推奨します：

```python
import json
from collections import OrderedDict

# response.jsonlを読み込んで、各IDの最新エントリのみを保持
entries_by_id = OrderedDict()

with open('response.jsonl', 'r') as f:
    for line in f:
        if not line.strip():
            continue
        data = json.loads(line)
        entry_id = data.get('id')
        if entry_id:
            entries_by_id[entry_id] = data  # 最新のエントリで上書き

# 重複を除去した結果を保存
with open('response_deduplicated.jsonl', 'w') as f:
    for entry in entries_by_id.values():
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')
```

### 2. 統計の再計算

重複を除去した後、統計情報を再計算することを推奨します。

### 3. 処理中断の防止

今後の評価実行時は、以下を推奨します：

1. **長時間実行の準備**: 評価が完了するまでPCを閉じない
2. **バックグラウンド実行**: `nohup`や`screen`を使用してバックグラウンドで実行
3. **チェックポイント機能の活用**: 既に実装されているチェックポイント機能により、中断後も再開可能

## まとめ

1. **boxed抽出エラー**: なし
2. **処理中断の影響**: 重複エントリが144件発生
3. **対応**: 最新エントリのみを使用するように重複を除去

**主要な問題は、API呼び出しの失敗（`solution=null`）であり、boxed抽出の問題ではありません。**
