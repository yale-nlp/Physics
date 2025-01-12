import os
import base64
import json
from dotenv import load_dotenv
from openai import OpenAI  # 假设已安装 openai 客户端库
import extract_boxed
import equation_equivilancy
import time

# 加载环境变量
load_dotenv()

# 初始化 OpenAI 客户端
os.environ["OPENAI_BASE_URL"] = "https://yanlp.zeabur.app/v1"
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
client = OpenAI()

def ask_llm_with_retries(llm_messages, max_retries=3, delay=2):
    """
    询问 LLM，最多重试 max_retries 次。

    Args:
        llm_messages (list): LLM 消息内容。
        max_retries (int): 最大重试次数。
        delay (int): 每次重试之间的延迟（秒）。

    Returns:
        str: LLM 的响应，或者 None 如果所有尝试都失败。
    """
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=llm_messages
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(delay)
    print("All attempts to get a valid response from LLM failed.")
    return None

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
            dataset_answers = data.get("final_answers", [])

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

            # Retry to get valid response
            answers = ask_llm_with_retries(messages)
            if answers is None:
                print(f"Skipping entry ID {entry_id} due to repeated failures.")
                continue

            retry_attempts = 3
            for attempt in range(retry_attempts):
                # Extract final answers from the solution
                llm_final_answers = extract_boxed.extract_final_answer_allform(answers, answer_type='list')
                if llm_final_answers:
                    break
                print(f"No boxed content found in attempt {attempt + 1}. Retrying...")

                answers = ask_llm_with_retries(messages)
                if answers is None:
                    print(f"Skipping entry ID {entry_id} due to repeated failures during retries.")
                    break

            if not llm_final_answers:
                print(f"Skipping entry ID {entry_id} due to missing boxed content after retries.")
                continue
            
            flattened_answers = [item for sublist in llm_final_answers for item in sublist] if isinstance(llm_final_answers[0], list) else llm_final_answers


            # Compare answers and calculate accuracy
            correct_count = 0
            for llm_answer in flattened_answers:
                if any(equation_equivilancy.is_equiv(llm_answer, dataset_answer) for dataset_answer in dataset_answers):
                    correct_count += 1

            total_comparisons = len(flattened_answers)
            accuracy = correct_count / total_comparisons if total_comparisons > 0 else 0.0


            # Append results to list
            results.append({
                "id": entry_id,
                "solution": answers,
                "final_answers": flattened_answers,
                "correct": accuracy
            })

            print(f"Answers processed for entry ID {entry_id}. Correct: {accuracy:.2f}")

    # Save all results to the output JSONL file
    with open(output_jsonl, "w") as outfile:
        for result in results:
            outfile.write(json.dumps(result, ensure_ascii=False) + "\n")

    print(f"All answers saved to {output_jsonl}.")


# Example Usage
input_jsonl = "test_dataset.jsonl"  # JSONL file with id, questions, solutions, and graphs
output_jsonl = "test_llm_response.jsonl"  # JSONL file to save answers

process_jsonl_and_generate_answers(input_jsonl, output_jsonl)
