import re

def extract_all_boxed_content(latex_response, latex_wrap=r'\\boxed{([^{}]*|{.*?})}'):
    """
    Extract all \boxed{} content from a LaTeX response, supporting nested {}.

    Args:
        latex_response (str): The LaTeX response text.
        latex_wrap (str): Regular expression pattern for matching \boxed{}.

    Returns:
        list: Extracted \boxed{} content.
    """
    # Define regex pattern to match nested \boxed{}
    pattern = re.compile(r'\\boxed{((?:[^{}]|{(?:[^{}]|{.*?})*})*)}|\\\\\[boxed{((?:[^{}]|{(?:[^{}]|{.*?})*})*)}\\\\\]', re.DOTALL)
    matches = pattern.findall(latex_response)  # Match all occurrences

    if not matches:
        return []
    # Flatten matches and remove empty strings
    return [match.strip() for sublist in matches for match in sublist if match.strip()]

def extract_final_answer(last_answer):
    """
    Extract the final answer from \boxed{}.

    Args:
        last_answer (str): LaTeX text containing \boxed{}.

    Returns:
        str: Extracted answer.
    """
    match = re.search(r'\\boxed{(.*?)}|\\\\\[boxed{(.*?)}\\\\\]', last_answer)
    if match:
        return next(group for group in match.groups() if group).strip()
    return last_answer

def extract_final_answer_list(last_answer):
    """
    Extract a list of answers from \boxed{} (for multi-part answers).

    Args:
        last_answer (str): LaTeX text containing \boxed{}.

    Returns:
        list: Extracted list of answers.
    """
    matches = re.findall(r'\\boxed{\\\[(.*?)\\\]}|\\\\\[boxed{\\\[(.*?)\\\]}\\\\\]', last_answer)
    if matches:
        return [item.strip() for sublist in matches for item in sublist if item for item in item.split(',')]
    return [extract_final_answer(last_answer)]

def extract_final_answer_allform(latex_response, answer_type=None, latex_wrap=r'\\boxed{(.*?)}'):
    """
    General method to extract all final answers.

    Args:
        latex_response (str): LaTeX response text.
        answer_type (str): Type of answer (float, list, math_expression).
        latex_wrap (str): Regular expression pattern for matching LaTeX content.

    Returns:
        list: Extracted answers.
    """
    boxed_content = extract_all_boxed_content(latex_response, latex_wrap)
    if not boxed_content:
        return []

    if answer_type == 'list':
        return [extract_final_answer_list(item) for item in boxed_content]
    return [extract_final_answer(item) for item in boxed_content]
