from openai import OpenAI
import subprocess
import os
import re
import pickle

# Initialize OpenAI client
os.environ["OPENAI_BASE_URL"] = "https://yanlp.zeabur.app/v1"
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
client = OpenAI()

def extract_python_code(content):
    """
    Extract Python code enclosed in ```python ``` tags from the content.
    If no such tags are found, return the entire content.
    """
    code_blocks = re.findall(r"```python\s+(.*?)```", content, re.DOTALL)
    if code_blocks:
        return "\n".join(code_blocks).strip()
    return content.strip()

def generate_code(problem_description):
    """
    Generate Python code to solve a physics problem using GPT model
    """
    # Construct the message prompt
    messages = [
        {
            "role": "system",
            "content": "You are a physicist and programmer specializing in solving physics problems using Python."
        },
        {
            "role": "user",
            "content": f"""
            Please generate Python code to solve the following physics problem:
            Problem: {problem_description}
            
            Requirements:
            1. Use the `sympy` library for symbolic computation.
            2. Save the final answer in standard latex format to a file named `result.pkl` using the `pickle` library.
            3. Ensure the code is well-commented to explain each step.
            4. Do not print any result in the code; only save it to the pickle file.
            """
        }
    ]
    
    try:
        # Call OpenAI GPT model to generate code
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages
        )
        generated_content = response.choices[0].message.content.strip()
        return extract_python_code(generated_content)
    except Exception as e:
        print(f"Error during code generation: {e}")
        return None

def save_code_to_file(code, filename="generated_solution.py"):
    """
    Save the extracted code to a local file
    """
    try:
        with open(filename, "w", encoding="utf-8") as file:
            file.write(code)
        print(f"Code has been saved to the file: {filename}")
    except Exception as e:
        print(f"Error saving the code: {e}")

def run_python_code(filename="generated_solution.py"):
    """
    Automatically run the extracted Python code
    """
    try:
        result = subprocess.run(['python', filename], capture_output=True, text=True)
        if result.stderr:
            print("\nExecution Errors:")
            print(result.stderr)
    except Exception as e:
        print(f"Error during code execution: {e}")

def load_pickle_result(filename="result.pkl"):
    """
    Load and display the content of the pickle file
    """
    try:
        with open(filename, 'rb') as f:
            result = pickle.load(f)
        print("\nContent of the pickle file:")
        print(result)
    except Exception as e:
        print(f"Error loading pickle file: {e}")

def main():
    # Input the physics problem
    problem_description = input("Please describe the physics problem: ")
    
    # Generate the code
    code = generate_code(problem_description)
    if not code:
        print("Code generation failed. Please check the problem description or API settings.")
        return
    
    # Save the code to a file
    filename = "generated_solution.py"
    save_code_to_file(code, filename)
    
    # Run the generated code
    run_python_code(filename)
    
    # Load and display the pickle file content
    load_pickle_result()

if __name__ == "__main__":
    main()
