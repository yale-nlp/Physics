import re
import math
import os
import csv

def count_md_equations(file_path):
    """
    统计 Markdown 文件中的公式数量，并计算费用明细。
    :param file_path: Markdown 文件路径。
    :return: 一个包含行间公式数量、行内公式数量、总公式数量及费用明细的字典。
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 匹配行间公式 $$...$$，忽略 tag 信息
    block_formula_pattern = re.compile(r'\$\$(.*?)\$\$', re.DOTALL)

    # 按逻辑分段统计行间公式的块数
    def count_block_formula_segments(match):
        formula_content = match.group(1).strip()
        formula_content = re.sub(r'\\tag\{.*?\}', '', formula_content)
        segments = [seg for seg in re.split(r'(?<!\\)\\\\|\n', formula_content) if seg.strip()]
        return len(segments)

    block_formula_matches = list(block_formula_pattern.finditer(content))
    block_formula_count = sum(count_block_formula_segments(match) for match in block_formula_matches)

    # 匹配行内公式 $公式$
    inline_formula_pattern = re.compile(r'(?<!\\)\$(?!\$)(.*?)(?<!\\)\$')
    inline_formula_matches = inline_formula_pattern.findall(content)

    # 清理嵌套干扰
    inline_formula_matches_cleaned = [m for m in inline_formula_matches if not re.search(r'\$.*\$', m)]
    inline_formula_count = len(inline_formula_matches_cleaned)

    # 行内公式折算为行间公式
    inline_as_block_count = math.ceil(inline_formula_count / 4)

    # 总公式数量
    total_formula_count = block_formula_count + inline_as_block_count

    # 计算费用
    if total_formula_count <= 8:
        cost = 4
    else:
        cost = 4 + (total_formula_count - 8) * 0.5

    return {
        "block_formula_count": block_formula_count,
        "inline_formula_count": inline_formula_count,
        "inline_as_block_count": inline_as_block_count,
        "total_formula_count": total_formula_count,
        "cost": cost
    }

def process_folder(folder_path, output_csv):
    """
    统计文件夹中所有子文件夹里的 questions.md 和 solutions.md 文件，保存统计结果到 CSV。
    :param folder_path: 文件夹路径。
    :param output_csv: 输出的 CSV 文件路径。
    """
    results = []

    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file in ["questions.md", "solutions.md"]:
                file_path = os.path.join(root, file)
                stats = count_md_equations(file_path)
                results.append({
                    "folder": os.path.basename(root),
                    "file": file,
                    **stats
                })

    # 保存到 CSV 文件
    with open(output_csv, mode='w', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            "folder", "file", "block_formula_count", "inline_formula_count", 
            "inline_as_block_count", "total_formula_count", "cost"
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    # 计算总和
    total = {
        "block_formula_count": sum(item["block_formula_count"] for item in results),
        "inline_formula_count": sum(item["inline_formula_count"] for item in results),
        "inline_as_block_count": sum(item["inline_as_block_count"] for item in results),
        "total_formula_count": sum(item["total_formula_count"] for item in results),
        "cost": sum(item["cost"] for item in results)
    }

    print("统计完成，结果已保存到", output_csv)
    print("总计:")
    for key, value in total.items():
        print(f"{key}: {value}")

if __name__ == "__main__":
    folder_path = ''
    output_csv = ''
    try:
        process_folder(folder_path, output_csv)
    except Exception as e:
        print("发生错误:", e)
