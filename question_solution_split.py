import os

def read_and_split_md_files_recursively(folder_path):
    """
    Recursively read all .md files in the given folder and its subfolders in alphanumeric order,
    and split their content into questions and solutions based on "SOLUTION:".

    Args:
        folder_path (str): Path to the folder containing .md files.

    Returns:
        dict: A dictionary where keys are relative folder paths and values are tuples of
              (combined questions, combined solutions).
    """
    result = {}

    # Recursively traverse the folder
    for root, _, files in os.walk(folder_path):
        # Sort files alphabetically
        md_files = sorted(
            [f for f in files if f.lower().endswith('.md')],
            key=lambda x: x.lower()
        )

        combined_questions = []
        combined_solutions = []

        for md_file in md_files:
            file_path = os.path.join(root, md_file)
            print(f"Processing file: {file_path}")

            # Read the content of the file
            with open(file_path, "r") as f:
                content = f.read()

            # Split the content into question and solution based on "SOLUTION:"
            if "SOLUTION:" in content:
                question, solution = content.split("SOLUTION:", 1)
                combined_questions.append(question.strip())
                combined_solutions.append(solution.strip())
            else:
                # If no "SOLUTION:" is found, consider the entire content as a question
                combined_questions.append(content.strip())

        # Store results by relative folder path
        relative_path = os.path.relpath(root, folder_path)
        result[relative_path] = ("\n\n".join(combined_questions), "\n\n".join(combined_solutions))

    return result


def save_combined_content_with_structure(result, input_folder, output_folder):
    """
    Save combined questions and solutions to separate files while preserving folder structure.

    Args:
        result (dict): A dictionary where keys are relative folder paths and values are tuples of
                       (combined questions, combined solutions).
        input_folder (str): Path to the input folder for reference.
        output_folder (str): Path to the output folder.
    """
    for relative_path, (questions, solutions) in result.items():
        # Create corresponding output folder
        target_folder = os.path.join(output_folder, relative_path)
        os.makedirs(target_folder, exist_ok=True)

        # Save questions
        question_file = os.path.join(target_folder, "combined_questions.md")
        solution_file = os.path.join(target_folder, "combined_solutions.md")

        try:
            # Save questions
            with open(question_file, "w") as qf:
                qf.write("# Combined Questions\n\n")
                qf.write(questions)
            print(f"Questions saved to: {question_file}")

            # Save solutions
            with open(solution_file, "w") as sf:
                sf.write("# Combined Solutions\n\n")
                sf.write(solutions)
            print(f"Solutions saved to: {solution_file}")
        except Exception as e:
            print(f"Error saving files in {target_folder}: {e}")


# Example Usage
# Folder path containing .md files
input_folder = "test_md_output"
output_folder = "test_combined_output"

# Read and split content
result = read_and_split_md_files_recursively(input_folder)

# Save combined content with structure
save_combined_content_with_structure(result, input_folder, output_folder)
