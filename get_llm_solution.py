import os
import base64
import json
from dotenv import load_dotenv
from openai import OpenAI  # 假设已安装 openai 客户端库
import extract_boxed

# 加载环境变量
load_dotenv()

# 初始化 OpenAI 客户端
os.environ["OPENAI_BASE_URL"] = "https://yanlp.zeabur.app/v1"
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
client = OpenAI()

def process_jsonl_and_generate_answers(input_jsonl, output_jsonl):
    """
    Process a JSONL file containing questions, solutions, and image graphs, send the data to LLM,
    and save the answers to an output JSONL file.

    Args:
        input_jsonl (str): Path to the JSONL file containing input data.
        output_jsonl (str): Path to the JSONL file where the answers will be saved.
    """
    results = []

    # Read JSONL file
    with open(input_jsonl, "r") as file:
        for line in file:
            data = json.loads(line.strip())

            # Extract fields
            entry_id = data.get("id")
            questions = data.get("questions", "")
            graphs = data.get("graphs", [])

            # Initialize LLM messages
            llm_messages = []

            # Add question content
            if questions:
                llm_messages.append({
                    "type": "text",
                    "text": questions
                })

            # Add graphs (images)
            if graphs:
                llm_messages.extend(graphs)

            # Skip empty messages
            if not llm_messages:
                continue

            print(f"Processing entry ID: {entry_id}...")

            # LLM Prompt
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an AI expert specializing in answering advanced physics questions from multiple fields. A Physical question will be given. Show the process and provide the final answer. "
                        "Answer in standard markdown format with Latex. put final answer(s) text or equations inside a Latex boxed format \\[boxed{}\\].\n"
                        "exmaple: \\[ \\boxed{ final_answer} \\]]\n" 
                        "Think step by step."
                    },
                    {
                        "role": "user",
                        "content": llm_messages
                    }
                ]
            )

            # Extract the answer from the LLM response
            answers = response.choices[0].message.content.strip()

            # Extract final answers from the solution
            final_answers = extract_boxed.extract_final_answer_allform(answers, answer_type='list')

            # Append results to list
            results.append({
                "id": entry_id,
                "solution": answers,
                "final_answers": final_answers
            })

            print(f"Answers processed for entry ID {entry_id}.")

    # Save all results to the output JSONL file
    with open(output_jsonl, "w") as outfile:
        for result in results:
            outfile.write(json.dumps(result) + "\n")

    print(f"All answers saved to {output_jsonl}.")

# Example Usage
input_jsonl = "test_dataset.jsonl"  # JSONL file with id, questions, solutions, and graphs
output_jsonl = "test_llm_response.jsonl"  # JSONL file to save answers

process_jsonl_and_generate_answers(input_jsonl, output_jsonl)
