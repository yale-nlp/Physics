import json

def calculate_average_question_length(jsonl_file):
    total_length = 0
    total_questions = 0
    
    with open(jsonl_file, 'r', encoding='utf-8') as file:
        for line in file:
            data = json.loads(line)  # 解析 JSONL 中的每一行
            if 'questions' in data and isinstance(data['questions'], list):
                for question in data['questions']:
                    if isinstance(question, str):  # 确保问题是字符串
                        total_length += len(question)
                        total_questions += 1
    
    if total_questions == 0:
        return 0  # 避免除零错误
    
    return total_length / total_questions

# 示例调用
jsonl_file_path = 'your_dataset.jsonl'  # 替换为你的 JSONL 文件路径
average_length = calculate_average_question_length(jsonl_file_path)
print(f'平均问题长度: {average_length:.2f} 字符')
