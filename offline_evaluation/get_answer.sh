#!/bin/bash

# 确保脚本出错时退出
set -e

# 设置默认参数
MODEL_NAME="deepseek-ai/DeepSeek-R1-Distill-Qwen-32B"
DOWNLOAD_DIR="scratch"
OUTPUT_DIR="offline_outputs/DeepSeek_R1_Distill_Qwen_32B_outputs"
MAX_LINES=1500

# 定义数据集路径列表
DATASET_LIST=(
    "datasets/atomic_dataset_textonly.jsonl"
    "datasets/electro_dataset_textonly.jsonl"
    "datasets/mechanics_dataset_textonly.jsonl"
    "datasets/optics_dataset_textonly.jsonl"
    "datasets/quantum_dataset_textonly.jsonl"
    "datasets/statistics_dataset_textonly.jsonl"
)

# 确保双引号闭合，传递正确的参数
nohup python get_answer.py \
    --model_name "$MODEL_NAME" \
    --download_dir "$DOWNLOAD_DIR" \
    --output_dir "$OUTPUT_DIR" \
    --max_lines "$MAX_LINES" \
    --dataset_list "${DATASET_LIST[@]}" > get_answer.out 2>&1 &
