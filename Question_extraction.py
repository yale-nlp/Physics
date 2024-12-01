from openai import OpenAI
import base64
import os
os.environ["OPENAI_BASE_URL"] = "https://yanlp.zeabur.app/v1"
os.environ["OPENAI_API_KEY"] = "sk-UalnCx6d8J63A0cTAf3c3fA14a54499bA3Ce29A23cD1242b"
client = OpenAI()

# Function to extract text from an image
def extract_text_from_image(image_path, api_key):
    """
    Extract text from an image using GPT-4o API.

    Args:
        image_path (str): Path to the image file.
        api_key (str): Your OpenAI API key.

    Returns:
        str: Extracted text from the image.
    """
    try:
        # Read the image and encode it in base64
        with open(image_path, 'rb') as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode('utf-8')

        # Set up the OpenAI API key
        client.api_key = api_key

        
        # Send a request to GPT-4o API to extract text from the image
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an assistant that extracts text from images."},
                {"role": "user", 
                 "content": [
                        {
                            "type": "text",
                            "text": "Extract the text from the image. convert all text and equations into standard markdown format.",
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url":  f"data:image/jpeg;base64,{encoded_image}"
                            },
                        }
                    ]
                }
            ]
        )

        # Extract text from the API response
        extracted_text = response.choices[0].message.content
        return extracted_text

    except Exception as e:
        return f"An unexpected error occurred: {e}"

def save_to_markdown(text, file_name="extracted_text.md"):
    """
    Save extracted text to a Markdown file.

    Args:
        text (str): Text to be saved.
        file_name (str): Name of the Markdown file.
    """
    try:
        with open(file_name, "w") as md_file:
            md_file.write("# Extracted Text\n\n")
            md_file.write(text)
        print(f"Extracted text saved to {file_name}")
    except Exception as e:
        print(f"Error saving to Markdown file: {e}")
        

def extract_text_from_images_in_folder(folder_path, api_key):
    # 获取文件夹中所有以 .jpg 结尾的文件
    jpg_files = [f for f in os.listdir(folder_path) if f.endswith('.jpg')]
    
    for jpg_file in jpg_files[:5]:
        image_path = os.path.join(folder_path, jpg_file)
        
        print(f"Processing file: {jpg_file}")
        
        # 提取图像中的文本
        extracted_text = extract_text_from_image(image_path, api_key)
        
        # 将提取的文本保存到 Markdown 文件
        markdown_filename = 'md_output'+jpg_file.replace('.jpg', '.md')  # 将文件扩展名改为 .md
        save_to_markdown(extracted_text, markdown_filename)
        print(f"Saved extracted text to: {markdown_filename}")
        

if __name__ == "__main__":
    # 设置 API 密钥
    api_key = "sk-UalnCx6d8J63A0cTAf3c3fA14a54499bA3Ce29A23cD1242b"

    # 文件夹路径
    folder_path = "extracted_photos"  # 替换为你的文件夹路径

    # 遍历并处理文件夹中的所有 JPG 文件
    extract_text_from_images_in_folder(folder_path, api_key)
