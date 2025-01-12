import os
import json
import re
import base64
from dotenv import load_dotenv
from openai import OpenAI
import extract_boxed

# 加载环境变量
load_dotenv()

# 初始化 OpenAI 客户端
os.environ["OPENAI_BASE_URL"] = "https://yanlp.zeabur.app/v1"
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
client = OpenAI()

def read_file_content(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        return None
    
def extract_answers_from_md(question_content, md_content):
    """
    从 Markdown 文件内容中提取所有最终答案。

    Args:
        question_content (str): 问题内容。
        md_content (str): 解决方案内容。

    Returns:
        list: 提取的所有最终答案列表。
    """
    prompt = (
        f"Questions Content:\n{question_content}\n\n"
        f"Solutions Content:\n{md_content}\n\n"
        "Extract the final answer of each problem(s) in a SymPy convertible format, and put extracted final answer(s) text or equations inside a Latex boxed format \\[boxed{}\\].\n"
        "exmaple: \\[ \\boxed{C_v = c} \\]]\n"
    )

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are an assistant that extracts final answers from provided content."},
            {"role": "user", "content": prompt}
        ]
    )

    raw_content = response.choices[0].message.content.strip()
    print("Raw Content:", raw_content)

    return extract_boxed.extract_final_answer_allform(raw_content, answer_type='list')

def encode_png_to_data_url(folder_path):
    image_messages = []
    for file in sorted(os.listdir(folder_path)):
        if file.lower().endswith('.png') and re.match(r'^\d', file):
            image_path = os.path.join(folder_path, file)
            with open(image_path, "rb") as img_file:
                encoded_image = base64.b64encode(img_file.read()).decode("utf-8")
                image_messages.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{encoded_image}"
                    }
                })
    return image_messages

def process_folders_to_jsonl(input_folder, output_file):
    jsonl_data = []

    for root, dirs, files in os.walk(input_folder):
        for dir_name in dirs:
            folder_path = os.path.join(root, dir_name)
            questions_path = os.path.join(folder_path, 'questions.md')
            solutions_path = os.path.join(folder_path, 'solutions.md')

            questions_content = read_file_content(questions_path)
            solutions_content = read_file_content(solutions_path)

            # 查找 PNG 文件并转换为 Data URL 格式
            encoded_graphs = encode_png_to_data_url(folder_path)

            if questions_content is not None and solutions_content is not None:
                final_answers = extract_answers_from_md(questions_content, solutions_content)
                flattened_answers = [item for sublist in final_answers for item in sublist] if isinstance(final_answers[0], list) else final_answers

                jsonl_entry = {
                    "id": f"{input_folder}/{dir_name}",
                    "questions": questions_content,
                    "solutions": solutions_content,
                    "final_answers": flattened_answers
                }

                if encoded_graphs:
                    jsonl_entry["graphs"] = encoded_graphs
                else:
                    jsonl_entry["graphs"] = None

                jsonl_data.append(jsonl_entry)

    with open(output_file, 'w', encoding='utf-8') as output:
        for entry in jsonl_data:
            output.write(json.dumps(entry, ensure_ascii=False) + '\n')

# 示例用法
if __name__ == "__main__":
    input_folder = 'test_examples'  # 替换为你的主文件夹路径
    output_file = 'test_dataset.jsonl'  # 输出文件路径
    process_folders_to_jsonl(input_folder, output_file)
    print(f"JSONL文件已生成: {output_file}")
