import openai
import json
import os
import re
os.environ["OPENAI_BASE_URL"] = "https://yanlp.zeabur.app/v1"


# Set up OpenAI API key
openai.api_key = "sk-UalnCx6d8J63A0cTAf3c3fA14a54499bA3Ce29A23cD1242b"



def ask_gpt(question: str, prompt: str, model: str = "gpt-4o"):
    """
    Query the GPT model with a physics question.

    Args:
        question (str): The physics question to ask.
        prompt (str): The prompt to instruct GPT's response format.
        model (str): The OpenAI GPT model to use (default is "gpt-4o").

    Returns:
        str: The model's response.
    """
    try:
        response = openai.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": question},
            ],
            max_tokens=1500,  # Adjust as needed
            temperature=0.1,  # Controls randomness
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"An error occurred: {e}"


def extract_equations_with_gpt(answer: str):
    """
    Use GPT to extract text and equations from the GPT answer.

    Args:
        answer (str): The GPT-generated answer.
        model (str): The GPT model to use for formula extraction.

    Returns:
        dict: A dictionary categorizing text and equations.
    """
    prompt = (
        "You are an assistant specializing in parsing and categorizing content. "
        "Given the following text, extract all equations and convert into standard markdown format. Put all equations in Latex format that can be read by markdown.$...$ for inline formulas and $$...$$ for block formulas. "
    )
    try:
        response = openai.chat.completions.create(
            model='gpt-4o',
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": answer},
            ],
            max_tokens=1500,
            temperature=0.1,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"An error occurred while extracting equations: {e}")
        return {}


def save_answer_to_json(question: str, answer: str, equations: dict, filename: str = "gpt-4o_output.json"):
    """
    Save the question, answer, and equations to a JSON file.

    Args:
        question (str): The physics question.
        answer (str): The answer provided by GPT.
        equations (dict): Categorized equations.
        filename (str): The filename for the JSON file.
    """
    data = {
        "question": question,
        "answer": answer,
        "equations": equations
    }
    try:
        # Check if the file exists and is not empty
        if os.path.exists(filename) and os.path.getsize(filename) > 0:
            with open(filename, "r", encoding="utf-8") as file:
                try:
                    file_data = json.load(file)
                except json.JSONDecodeError:
                    print(f"Warning: {filename} is invalid or corrupted. Starting fresh.")
                    file_data = []
        else:
            file_data = []

        # Append the new data
        file_data.append(data)

        # Write back to the JSON file
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(file_data, file, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"An error occurred while saving to JSON: {e}")


def read_questions_from_json(filename: str):
    """
    Read the questions from a JSON file.

    Args:
        filename (str): Path to the JSON file.

    Returns:
        list: A list of questions extracted from the JSON file.
    """
    try:
        with open(filename, "r", encoding="utf-8") as file:
            data = json.load(file)
            return [element["question"] for element in data if "question" in element]
    except Exception as e:
        print(f"An error occurred while reading {filename}: {e}")
        return []


if __name__ == "__main__":
    json_file = "example.json"
    model = "meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo"
    modified_pathname = re.sub(r"/", "-", model)
    print(modified_pathname)

    # Read questions from the JSON file
    questions = read_questions_from_json(json_file)
    prompt = (
        "You are an AI expert specializing in answering advanced physics questions from multiple fields. "
        "A physics question will be given. Please provide the answer to the question. "
        "Think step by step. "
    )

    # Process each question
    for question in questions:

        # Get the GPT answer
        answer = ask_gpt(question, prompt, model)

        # Use GPT to extract equations
        equations = extract_equations_with_gpt(answer)

        # Save to JSON
        
        save_answer_to_json(question, answer, equations, filename=f"output/{modified_pathname}_output.json")
    print('response achieved')

