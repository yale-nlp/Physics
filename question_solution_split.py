import os
def extract_questions_and_solutions_from_merged(output_folder):
    """
    Extract questions and solutions from merged_content.md and save to the same folder structure.

    Args:
        output_folder (str): Path to the folder containing merged_content.md files.
    """
    for root, _, files in os.walk(output_folder):
        if "merged_content.md" in files:
            file_path = os.path.join(root, "merged_content.md")
            print(f"Processing merged file: {file_path}")

            # Read merged content
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Split content into questions and solutions
            if "SOLUTION:" in content:
                question, solution = content.split("SOLUTION:", 1)
            else:
                question = content
                solution = ""

            # Save questions and solutions
            question_file = os.path.join(root, "questions.md")
            solution_file = os.path.join(root, "solutions.md")

            try:
                # Save questions
                with open(question_file, "w", encoding="utf-8") as qf:
                    qf.write("# Questions\n\n")
                    qf.write(question.strip())
                print(f"Questions saved to: {question_file}")

                # Save solutions
                with open(solution_file, "w", encoding="utf-8") as sf:
                    sf.write("# Solutions\n\n")
                    sf.write(solution.strip())
                print(f"Solutions saved to: {solution_file}")
            except Exception as e:
                print(f"Error saving questions or solutions in {root}: {e}")


# Example Usage
output_folder = "test_processed_questions"
# Extract questions and solutions from merged_content.md
extract_questions_and_solutions_from_merged(output_folder)
