#!/bin/bash

# 确保脚本出错时退出
set -e

# 设置默认参数
MODEL_NAME="deepseek-ai/DeepSeek-R1-Distill-Qwen-32B"
DOWNLOAD_DIR="scratch/kaiyue_hf_cache"
OUTPUT_DIR="project/Kaiyue/offline_outputs/DeepSeek_R1_Distill_Qwen_32B_outputs"
MAX_LINES=1500

# 定义数据集路径列表
DATASET_LIST=(
    "project/Kaiyue/datasets/atomic_dataset_textonly.jsonl"
    "project/Kaiyue/datasets/electro_dataset_textonly.jsonl"
    "project/Kaiyue/datasets/mechanics_dataset_textonly.jsonl"
    "project/Kaiyue/datasets/optics_dataset_textonly.jsonl"
    "project/Kaiyue/datasets/quantum_dataset_textonly.jsonl"
    "project/Kaiyue/datasets/statistics_dataset_textonly.jsonl"
)

# 确保双引号闭合，传递正确的参数
nohup ~/miniconda3/envs/kaiyue/bin/python project/Kaiyue/get_answer.py \
    --model_name "$MODEL_NAME" \
    --download_dir "$DOWNLOAD_DIR" \
    --output_dir "$OUTPUT_DIR" \
    --max_lines "$MAX_LINES" \
    --dataset_list "${DATASET_LIST[@]}" > get_answer.out 2>&1 &
