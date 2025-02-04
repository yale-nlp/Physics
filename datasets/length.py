import json
import os
import re

def calculate_average_question_length(folder_path):
    total_length = 0
    total_questions = 0
    
    for filename in os.listdir(folder_path):
        if filename.endswith('.jsonl'):
            file_path = os.path.join(folder_path, filename)
            with open(file_path, 'r', encoding='utf-8') as file:
                for line in file:
                    data = json.loads(line)  # 解析 JSONL 中的每一行
                    if 'solutions' in data and isinstance(data['solutions'], str):
                        # 处理 LaTeX 公式，将其视为单个字符
                        cleaned_question = re.sub(r'\$.*?\$', 'X', data['solutions'])  # 用 'X' 替换 LaTeX 公式
                        cleaned_question = re.sub(r'\s+', ' ', cleaned_question).strip()  # 移除换行符和多余空格
                        total_length += len(cleaned_question)
                        total_questions += 1
    
    if total_questions == 0:
        return 0  # 避免除零错误
    
    return total_length / total_questions

# 示例调用
folder_path = 'datasets'  # 替换为你的 JSONL 文件夹路径
average_length = calculate_average_question_length(folder_path)
print(f'平均问题长度: {average_length:.2f} 字符')