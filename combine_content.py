import os

def read_and_merge_md_files_by_folder(folder_path, output_folder):
    """
    Read all .md files in each folder and merge their content into merged_content.md,
    saved to the new output folder.

    Args:
        folder_path (str): Path to the folder containing .md files.
        output_folder (str): Path to the output folder where merged_content.md is saved.
    """
    # Recursively traverse the folder
    for root, _, files in os.walk(folder_path):
        # Sort files alphabetically
        md_files = sorted(
            [f for f in files if f.lower().endswith('.md')],
            key=lambda x: x.lower()
        )

        combined_content = []

        for md_file in md_files:
            file_path = os.path.join(root, md_file)
            print(f"Processing file: {file_path}")

            # Read the content of the file
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                combined_content.append(content)

        # Save combined content
        if combined_content:
            # Create corresponding output folder in the new structure
            relative_path = os.path.relpath(root, folder_path)
            target_folder = os.path.join(output_folder, relative_path)
            os.makedirs(target_folder, exist_ok=True)
            merged_file_path = os.path.join(target_folder, "merged_content.md")

            try:
                with open(merged_file_path, "w", encoding="utf-8") as f:
                    f.write("\n\n".join(combined_content))
                print(f"Merged content saved to: {merged_file_path}")
            except Exception as e:
                print(f"Error saving merged content in {target_folder}: {e}")


# Example Usage
input_folder = "test_md_files"
output_folder = "test_processed_questions"

# Merge .md files and save to the new folder
read_and_merge_md_files_by_folder(input_folder, output_folder)
