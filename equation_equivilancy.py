from sympy import simplify, Eq
from sympy.parsing.latex import parse_latex
import re

def _extract_core_eq(expr: str) -> str:
    """
    从复杂表达式中提取核心数学关系或等式的右侧部分。
    """
    # 如果包含 '='，提取等式右侧部分
    if "=" in expr:
        parts = expr.split("=")
        expr = parts[-1].strip()  # 提取等式右侧部分
    # 如果包含 \implies 或其他逻辑符号，提取逻辑符号后的部分
    if "\\implies" in expr:
        parts = expr.split("\\implies")
        expr = parts[-1].strip()
    return expr

def _preprocess_latex(string: str) -> str:
    """
    对 LaTeX 表达式进行预处理，移除排版符号、修复常见格式问题。
    """
    if not string:
        return ""
    
    # 替换双反斜杠为单反斜杠
    string = string.replace("\\\\", "\\")
    # 替换 \tfrac 和 \dfrac 为 \frac
    string = string.replace("tfrac", "frac").replace("dfrac", "frac")
    # 移除 \left 和 \right
    string = string.replace("\\left", "").replace("\\right", "")
    # 修复简单的 \sqrt3 -> \sqrt{3}
    string = re.sub(r"\\sqrt(\w)", r"\\sqrt{\1}", string)
    # 修复简单的 \frac1b -> \frac{1}{b}
    string = re.sub(r"\\frac(\w)(\w)", r"\\frac{\1}{\2}", string)
    # 修复简单的 a/b -> \frac{a}{b}
    string = re.sub(r"(\d+)/(\d+)", r"\\frac{\1}{\2}", string)
    # 修复 \DeltaT -> \Delta\cdot T
    string = re.sub(r"\\Delta(\w)", r"\\Delta\\cdot \1", string)
    # 移除右侧单位 \text{...}
    string = re.sub(r"\\text{.*?}", "", string)
    # 移除空格和换行符
    string = string.replace(" ", "").replace("\n", "")
    return string

def _extract_core_eq(expr):
    """
    从复杂表达式中提取核心数学关系或等式。
    """
    # 如果包含 \implies 或其他逻辑符号，进行分割提取
    if "\\implies" in expr:
        parts = expr.split("\\implies")
        # 默认提取最后一个部分作为目标表达式
        expr = parts[-1].strip()
    return expr

def is_equiv(expr1: str, expr2: str, verbose: bool = False) -> bool:
    """
    使用 SymPy 判断两个 LaTeX 表达式是否数学上等价，忽略等式左侧的变量名。
    """
    try:
        # 预处理字符串
        expr1 = _preprocess_latex(expr1)
        expr2 = _preprocess_latex(expr2)
        
        # 提取核心数学内容
        expr1 = _extract_core_eq(expr1)
        expr2 = _extract_core_eq(expr2)

        if verbose:
            print(f"Preprocessed Expr1: {expr1}")
            print(f"Preprocessed Expr2: {expr2}")
        
        # 使用 SymPy 解析为数学表达式
        sympy_expr1 = parse_latex(expr1)
        sympy_expr2 = parse_latex(expr2)

        if verbose:
            print(f"SymPy Expr1: {sympy_expr1}")
            print(f"SymPy Expr2: {sympy_expr2}")
        
        # 如果是 Eq 对象，提取右侧表达式
        if isinstance(sympy_expr1, Eq):
            sympy_expr1 = sympy_expr1.rhs  # 取等式右侧
        if isinstance(sympy_expr2, Eq):
            sympy_expr2 = sympy_expr2.rhs  # 取等式右侧

        # 比较右侧表达式是否数学等价
        return simplify(sympy_expr1 - sympy_expr2) == 0
    except Exception as e:
        if verbose:
            print(f"Error: {e}")
        return False

# 示例测试
if __name__ == "__main__":
    latex1 = r"\\text{Magnetic thermometer measures temperatures below } 1K"
    latex2 = r"\\text{Helium Gas Thermometer: Suitable down to } 1 \\, K"
    print(is_equiv(latex1, latex2, verbose=True))  # 输出: True

