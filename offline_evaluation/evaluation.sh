#!/bin/bash

# 确保脚本出错时退出
set -e

# 定义Python脚本的完整路径
PYTHON_SCRIPT="miniconda3/envs/kaiyue/bin/python"
SCRIPT_PATH="project/Kaiyue/evaluation.py"

# 确保环境变量和路径正确加载
export PATH="~/miniconda3/envs/kaiyue/bin:$PATH"

# 启动Python脚本，后台运行并记录日志，确保即使前台退出仍继续执行
nohup $PYTHON_SCRIPT $SCRIPT_PATH > final_eva.out 2>&1 &
