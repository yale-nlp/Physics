from sympy import simplify, expand, Eq, symbols, trigsimp
from sympy.parsing.latex import parse_latex
import re
import os
from openai import OpenAI

# Initialize OpenAI client
os.environ["OPENAI_BASE_URL"] = "https://yanlp.zeabur.app/v1"
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
client = OpenAI()


def _extract_core_eq(expr: str) -> str:
    """
    Extract the right-hand side of an equation or implication from a LaTeX expression.
    Handles cases where '=' and '\\implies' appear together.
    """
    # Handle implications first
    if "\\implies" in expr:
        parts = expr.split("\\implies")
        expr = parts[-1].strip()  # Keep the right-hand side of the implication
    
    # Then handle equations
    if "=" in expr:
        parts = expr.split("=")
        expr = parts[-1].strip()  # Keep the right-hand side of the equation
    
    return expr


def _preprocess_latex(string: str) -> str:
    """Preprocess LaTeX to normalize format and separate variables."""
    if not string:
        return ""
    
    def fix_fracs(string):
        substrs = string.split("\\frac")
        new_str = substrs[0]
        if len(substrs) > 1:
            substrs = substrs[1:]
            for substr in substrs:
                new_str += "\\frac"
                if substr[0] == "{":
                    new_str += substr
                else:
                    if len(substr) >= 2:
                        a, b = substr[0], substr[1]
                        if b != "{":
                            new_str += f"{{{a}}}{{{b}}}" + substr[2:]
                        else:
                            new_str += f"{{{a}}}" + b + substr[2:]
                    else:
                        new_str += substr
        return new_str
    
    def fix_sqrt(string):
        if "\\sqrt" not in string:
            return string
        splits = string.split("\\sqrt")
        new_string = splits[0]
        for split in splits[1:]:
            if split[0] != "{":
                a = split[0]
                new_substr = f"\\sqrt{{{a}}}" + split[1:]
            else:
                new_substr = "\\sqrt" + split
            new_string += new_substr
        return new_string

    # Normalize common issues
    string = re.sub(r"_\{.*?\}", "", string)
    string = re.sub(r"_\\?\w", "", string)
    string = string.replace("\\\\", "\\").replace("tfrac", "frac").replace("dfrac", "frac")
    string = string.replace("\\left", "").replace("\\right", "").replace("\\cdot", "*")

    # Separate variables and symbols
    string = re.sub(r"([a-zA-Z])\\([a-zA-Z])", r"\1 * \2", string)  # Separate adjacent variables and Greek letters
    string = re.sub(r"(\\[a-zA-Z]+)([a-zA-Z])", r"\1 * \2", string)  # Separate Greek letters and variables

    # Handle fractions and square roots
    string = fix_fracs(string)
    string = fix_sqrt(string)

    return string

def _standardize_expr(expr):
    """Standardize a SymPy expression."""
    return simplify(expand(trigsimp(expr)))

def call_llm_to_compare(expr1: str, expr2: str) -> bool:
    """
    Use an LLM to determine if two LaTeX expressions with text are equivalent.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an assistant that compares LaTeX expressions for equivalence."},
                {"role": "user", "content": f"Compare the following LaTeX expressions and check if they are mathmatically equivalent content:\n\nExpression 1:\n{expr1}\n\nExpression 2:\n{expr2}\n\n Do not assume anything. Return True if they are equivalent, otherwise return False."}
            ]
        )
        llm_result = response.choices[0].message.content
        return "true" in llm_result.lower()
    except Exception as e:
        print(f"Error calling LLM: {e}")
        return False






def is_equiv(expr1: str, expr2: str, verbose: bool = False) -> dict:
    """
    Compare two LaTeX expressions for equivalence.
    Returns results in a dictionary format.
    """
    result_data = {
        "input_expressions": {"expr1": expr1, "expr2": expr2},
        "preprocessed_expressions": {"expr1": "", "expr2": ""},
        "sympy_result": None,
        "llm_result": None,
        "final_result": None,
    }

    try:
        # If expressions contain text, delegate to LLM
        if "\\text" in expr1 or "\\text" in expr2:
            if verbose:
                print("Detected \\text. Delegating comparison to LLM.")
            llm_result = call_llm_to_compare(expr1, expr2)
            result_data["llm_result"] = llm_result
            result_data["final_result"] = llm_result
            return result_data

        # Preprocess LaTeX expressions
        expr1_processed = _preprocess_latex(expr1)
        expr2_processed = _preprocess_latex(expr2)

        # Extract core mathematical content
        expr1_core = _extract_core_eq(expr1_processed)
        expr2_core = _extract_core_eq(expr2_processed)

        # Parse into SymPy objects
        sympy_expr1 = _standardize_expr(parse_latex(expr1_core))
        sympy_expr2 = _standardize_expr(parse_latex(expr2_core))
        result_data["preprocessed_expressions"] = {"expr1": str(sympy_expr1), "expr2": str(sympy_expr2)}

        # SymPy comparison
        try:
            sympy_result = simplify(sympy_expr1 - sympy_expr2) == 0
        except Exception as e:
            sympy_result = False

        # If simplify fails, try symbolic equality check
        if not sympy_result:
            try:
                sympy_result = sympy_expr1.equals(sympy_expr2)
            except Exception:
                sympy_result = False

        result_data["sympy_result"] = sympy_result

        # Delegate to LLM if SymPy fails
        if not sympy_result:
            if verbose:
                print("SymPy result is False. Delegating to LLM for further evaluation.")
            llm_result = call_llm_to_compare(expr1, expr2)
            result_data["llm_result"] = llm_result
            result_data["final_result"] = llm_result
        else:
            result_data["final_result"] = sympy_result

    except Exception as e:
        if verbose:
            print(f"Error: {e}")
        result_data["error"] = str(e)

    return result_data

# Example tests
if __name__ == "__main__":
    # Example 1: Mathematical expressions
    latex1 = r"x = \sqrt{2 \mu h R}"
    latex2 = r"\sqrt{2\mu Rh}"
    result = is_equiv(latex1, latex2, verbose=True)
    print(result)

    # Example 2: Expressions with text
    latex3 = r"\\text{Vapor pressure thermometer measures temperatures greater than } 14K"
    latex4 = r"\\text{The temperatures should be greater than 14 kelvin for the vapor pressure thermometer to work}"
    result = is_equiv(latex3, latex4, verbose=True)
    print(result)