import os
from dotenv import load_dotenv
from openai import OpenAI  # 假设已安装 openai 客户端库

# 加载环境变量
load_dotenv()

# 设置 OpenAI 配置
os.environ["OPENAI_BASE_URL"] = "https://yanlp.zeabur.app/v1"
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

# 初始化 OpenAI 客户端
client = OpenAI()

def process_combined_questions_with_llm(input_folder, output_folder):
    """
    Process combined_questions.md files, send the entire content to LLM,
    and save the answers in corresponding subfolders while maintaining folder structure.

    Args:
        input_folder (str): Path to the folder containing combined_questions.md files.
        output_folder (str): Path to the folder where the answers will be saved.
    """
    # Traverse the input folder and find all combined_questions.md files
    for root, _, files in os.walk(input_folder):
        if "combined_questions.md" in files:
            input_file_path = os.path.join(root, "combined_questions.md")
            print(f"Processing file: {input_file_path}")

            # Read the combined_questions.md file as a single string
            with open(input_file_path, "r") as f:
                questions = f.read().strip()

            # Prepare the output folder for answers
            relative_path = os.path.relpath(root, input_folder)
            answer_folder = os.path.join(output_folder, relative_path)
            os.makedirs(answer_folder, exist_ok=True)

            # Answer file path
            answer_file_path = os.path.join(answer_folder, "answers.md")

            print("Sending entire questions.md content to LLM...")

            # LLM Prompt
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", 
                     "content": "You are an AI expert specializing in answering advanced physics questions from multiple fields. A set of physics questions will be given. Please provide answers to all questions in the same order as presented. For each question, show the process and provide the final answer. Think step by step."},
                    {"role": "user", "content": questions}
                ]
            )

            # Extract the answer from the LLM response
            answers = response.choices[0].message.content.strip()

            # Save the answers to the corresponding answers.md file
            with open(answer_file_path, "w") as f:
                f.write("# Answers\n\n")
                f.write(answers)

            print(f"Answers saved to: {answer_file_path}")


# Example Usage
input_folder = "test_combined_output"  # Folder with combined_questions.md
output_folder = "test_llm_answers"  # Folder to save answers

process_combined_questions_with_llm(input_folder, output_folder)
