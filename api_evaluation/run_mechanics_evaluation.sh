#!/bin/bash

# 力学データセット評価実行スクリプト
# 
# 使用方法:
#   bash run_mechanics_evaluation.sh
#
# 環境変数の設定が必要です:
#   - OPENAI_API_KEY (GPT-4o使用時)
#   - GEMINI_API_KEY (Gemini使用時)
#   - TOGETHER_API_KEY (DeepSeek-R1使用時)

set -e

# スクリプトのディレクトリに移動
cd "$(dirname "$0")"

echo "=========================================="
echo "力学データセット評価スクリプト"
echo "=========================================="
echo ""

# データセットの存在確認
if [ ! -f "../PHYSICS/mechanics_dataset.jsonl" ]; then
    echo "エラー: ../PHYSICS/mechanics_dataset.jsonl が見つかりません"
    exit 1
fi

echo "利用可能な評価スクリプト:"
echo "1) GPT-4o (evaluate_mechanics_gpt4o.py)"
echo "2) Gemini-1.5-Pro (evaluate_mechanics_gemini.py - 要作成)"
echo "3) Claude-3.5-Sonnet (evaluate_mechanics_claude.py - 要作成)"
echo ""

# デフォルトでGPT-4oを実行
echo "GPT-4oで評価を開始します..."
python evaluate_mechanics_gpt4o.py

echo ""
echo "評価が完了しました！"
echo "結果は ../outputs/gpt-4o_mechanics_output/ に保存されています。"




