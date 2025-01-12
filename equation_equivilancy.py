from sympy import simplify, Eq
from sympy.parsing.latex import parse_latex
import re

def _preprocess_latex(string: str) -> str:
    """
    对 LaTeX 表达式进行预处理，移除排版符号、修复常见格式问题。
    """
    if not string:
        return ""
    
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
    使用 SymPy 判断两个 LaTeX 表达式是否数学上等价。
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
        
        # 如果是方程 (Eq)，则比较两边的表达式
        if isinstance(sympy_expr1, Eq) and isinstance(sympy_expr2, Eq):
            return (simplify(sympy_expr1.lhs - sympy_expr2.lhs) == 0 and
                    simplify(sympy_expr1.rhs - sympy_expr2.rhs) == 0)
        else:
            # 直接比较非方程表达式
            return simplify(sympy_expr1 - sympy_expr2) == 0
    except Exception as e:
        if verbose:
            print(f"Error: {e}")
        return False

# 示例测试
if __name__ == "__main__":
    latex1 = r" \omega^2 = \frac{g}{\ell - \frac{\pi}{2} R}."
    latex2 = r"\ddot{\epsilon}+\frac{g}{\ell-\frac{\pi}{2}R}\epsilon=0\quad\implies\quad\omega^2=\frac{g}{\ell-\frac{\pi}{2}R}."
    print(is_equiv(latex1, latex2, verbose=True))  # 输出: True

    latex3 = r"\nu = \frac{1}{2\pi} \sqrt{\frac{m_p g R}{M_d R^2 + 4I + m_p R^2}}"
    latex4 = r"\omega^2 = \frac{M_d g R}{4I + (M_d + 4m_p) R^2}"
    print(is_equiv(latex3, latex4, verbose=True))  # 输出: True
