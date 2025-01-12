import re
import math

def count_md_equations(file_path):
    """
    统计 Markdown 文件中的公式数量，并计算费用明细。

    计算规则：
    - 行间公式每逻辑块按一条公式计算（$$或\[中的公式）。
    - 行内公式每4条 = 1条行间公式，向上取整。
    - 费用规则：
      - 8条以内总公式为4元
      - 超过8条，每条增加0.5元。
    
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
        # 去掉 tag 信息
        formula_content = re.sub(r'\\tag\{.*?\}', '', formula_content)
        segments = [seg for seg in re.split(r'(?<!\\)\\\\|\n', formula_content) if seg.strip()]
        return len(segments)

    block_formula_matches = list(block_formula_pattern.finditer(content))
    block_formula_count = sum(count_block_formula_segments(match) for match in block_formula_matches)

    # 打印行间公式及其逻辑块数
    print("行间公式:")
    for idx, match in enumerate(block_formula_matches):
        formula_content = re.sub(r'\\tag\{.*?\}', '', match.group(0))  # 去掉 tag 信息
        print(f"[{idx + 1}] 公式内容:")
        print(formula_content)
        print(f"逻辑块数: {count_block_formula_segments(match)} 条\n")

    # 匹配行内公式 $公式$
    inline_formula_pattern = re.compile(r'(?<!\\)\$(?!\$)(.*?)(?<!\\)\$')
    inline_formula_matches = inline_formula_pattern.findall(content)

    # 打印行内公式及其编号
    print("行内公式:")
    for idx, match in enumerate(inline_formula_matches):
        print(f"[{idx + 1}] 公式内容: {match}")

    # 调整对行内公式的统计逻辑，排除嵌套干扰
    inline_formula_matches_cleaned = [m for m in inline_formula_matches if not re.search(r'\$.*\$', m)]
    inline_formula_count = len(inline_formula_matches_cleaned)

    # 将行内公式每4条合并为1条行间公式，向上取整
    inline_as_block_count = math.ceil(inline_formula_count / 4)

    # 总公式数量
    total_formula_count = block_formula_count + inline_as_block_count

    # 计算费用明细
    if total_formula_count <= 8:
        cost = 4  # 基础费用
    else:
        cost = 4 + (total_formula_count - 8) * 0.5  # 超过8条，每条增加0.5元

    return {
        "block_formula_count": block_formula_count,
        "inline_formula_count": inline_formula_count,
        "inline_as_block_count": inline_as_block_count,
        "total_formula_count": total_formula_count,
        "cost": cost
    }

if __name__ == "__main__":
    file_path = input("请输入Markdown文件路径: ").strip()
    try:
        result = count_md_equations(file_path)
        print("统计结果:")
        print(f"行间公式数量: {result['block_formula_count']}")
        print(f"行内公式数量: {result['inline_formula_count']}")
        print(f"行内公式折算行间公式数量: {result['inline_as_block_count']}")
        print(f"总公式数量: {result['total_formula_count']}")
        print(f"费用明细: {result['cost']} 元")
    except FileNotFoundError:
        print("文件未找到，请检查文件路径。")
