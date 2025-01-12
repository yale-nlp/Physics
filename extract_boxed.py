import re

def extract_all_boxed_content(latex_response, latex_wrap=r'\\boxed{([^{}]*|{.*?})}'):
    """
    提取 LaTeX 响应中的所有 \boxed{} 内容，支持嵌套的 {}。

    Args:
        latex_response (str): 包含 LaTeX 的响应文本。
        latex_wrap (str): 匹配 \boxed{} 的正则表达式。

    Returns:
        list: 提取的所有 \boxed{} 内容。
    """
    # 定义正则表达式来匹配嵌套的 \boxed{}
    pattern = re.compile(r'\\boxed{((?:[^{}]|{(?:[^{}]|{.*?})*})*)}|\\\\\[boxed{((?:[^{}]|{(?:[^{}]|{.*?})*})*)}\\\\\]', re.DOTALL)
    matches = pattern.findall(latex_response)  # 匹配所有内容

    if not matches:
        print("No boxed content found in the response.")
        return []
    # Flatten matches and remove empty strings
    return [match.strip() for sublist in matches for match in sublist if match.strip()]

def extract_final_answer(last_answer):
    """
    从 \boxed{} 中提取最终答案。

    Args:
        last_answer (str): 包含 \boxed{} 的 LaTeX 文本。

    Returns:
        str: 提取的答案。
    """
    match = re.search(r'\\boxed{(.*?)}|\\\\\[boxed{(.*?)}\\\\\]', last_answer)
    if match:
        return next(group for group in match.groups() if group).strip()
    return last_answer

def extract_final_answer_list(last_answer):
    """
    提取 \boxed{} 中的答案列表（用于多部分答案）。

    Args:
        last_answer (str): 包含 \boxed{} 的 LaTeX 文本。

    Returns:
        list: 提取的答案列表。
    """
    matches = re.findall(r'\\boxed{\\[(.*?)\\]}|\\\\\[boxed{\\[(.*?)\\]}\\\\\]', last_answer)
    if matches:
        return [item.strip() for sublist in matches for item in sublist if item for item in item.split(',')]
    return [extract_final_answer(last_answer)]

def extract_final_answer_allform(latex_response, answer_type=None, latex_wrap=r'\\boxed{(.*?)}'):
    """
    通用方法，提取所有最终答案。

    Args:
        latex_response (str): 包含 LaTeX 的响应文本。
        answer_type (str): 答案类型（float, list, math_expression）。
        latex_wrap (str): 匹配 LaTeX 内容的正则表达式。

    Returns:
        list: 提取的所有答案。
    """
    boxed_content = extract_all_boxed_content(latex_response, latex_wrap)
    if not boxed_content:
        return []

    if answer_type == 'list':
        return [extract_final_answer_list(item) for item in boxed_content]
    return [extract_final_answer(item) for item in boxed_content]
