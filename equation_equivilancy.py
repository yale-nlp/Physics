from sympy import simplify, Eq
from sympy.parsing.latex import parse_latex
import re
import os
from openai import OpenAI

# Initialize OpenAI client
os.environ["OPENAI_BASE_URL"] = "https://yanlp.zeabur.app/v1"
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
client = OpenAI()

def _fix_fracs(string):
    substrs = string.split("\\frac")
    new_str = substrs[0]
    if len(substrs) > 1:
        substrs = substrs[1:]
        for substr in substrs:
            new_str += "\\frac"
            if substr[0] == "{":
                new_str += substr
            else:
                try:
                    assert len(substr) >= 2
                except:
                    return string
                a = substr[0]
                b = substr[1]
                if b != "{":
                    if len(substr) > 2:
                        post_substr = substr[2:]
                        new_str += "{" + a + "}{" + b + "}" + post_substr
                    else:
                        new_str += "{" + a + "}{" + b + "}"
                else:
                    if len(substr) > 2:
                        post_substr = substr[2:]
                        new_str += "{" + a + "}" + b + post_substr
                    else:
                        new_str += "{" + a + "}" + b
    string = new_str
    return string


def _fix_a_slash_b(string):
    if len(string.split("/")) != 2:
        return string
    a = string.split("/")[0]
    b = string.split("/")[1]
    try:
        a = int(a)
        b = int(b)
        assert string == "{}/{}".format(a, b)
        new_string = "\\frac{" + str(a) + "}{" + str(b) + "}"
        return new_string
    except:
        return string
    
def _fix_sqrt(string):
    if "\\sqrt" not in string:
        return string
    splits = string.split("\\sqrt")
    new_string = splits[0]
    for split in splits[1:]:
        if split[0] != "{":
            a = split[0]
            new_substr = "\\sqrt{" + a + "}" + split[1:]
        else:
            new_substr = "\\sqrt" + split
        new_string += new_substr
    return new_string

def _extract_core_eq(expr: str) -> str:
    """
    Extract the right-hand side of an equation or implication from a LaTeX expression.
    """
    if "=" in expr:
        parts = expr.split("=")
        expr = parts[-1].strip()
    if "\\implies" in expr:
        parts = expr.split("\\implies")
        expr = parts[-1].strip()
    return expr

def _preprocess_latex(string: str) -> str:
    """
    Preprocess LaTeX expressions to fix common issues and normalize the format.
    """
    if not string:
        return ""
    
    # Remove redundant LaTeX formatting
    string = string.replace("\\left", "").replace("\\right", "")
    string = string.replace("\\!", "").replace("\\$", "").replace("\\%", "")

    # Remove angle symbol
    string = string.replace("^{\\circ}", "").replace("^\\circ", "")

    # Normalize fractions and square roots
    string = _fix_fracs(string)
    string = _fix_a_slash_b(string)
    string = _fix_sqrt(string)

    # Fix decimal formatting
    string = string.replace(" .", " 0.").replace("{.", "{0.")
    if string.startswith("."):
        string = "0" + string

    # Remove units
    if "\\text{ " in string:
        splits = string.split("\\text{ ")
        if len(splits) == 2:
            string = splits[0]

    # Remove spaces
    string = string.replace(" ", "")

    return string


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
    Determine if two LaTeX expressions are mathematically or semantically equivalent.
    Returns results in a dictionary format for further analysis.
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
        result_data["preprocessed_expressions"] = {"expr1": expr1_processed, "expr2": expr2_processed}

        # Extract core mathematical content
        expr1_core = _extract_core_eq(expr1_processed)
        expr2_core = _extract_core_eq(expr2_processed)

        if verbose:
            print(f"Preprocessed Expr1: {expr1_core}")
            print(f"Preprocessed Expr2: {expr2_core}")

        # Parse expressions into SymPy objects
        sympy_expr1 = parse_latex(expr1_core)
        sympy_expr2 = parse_latex(expr2_core)

        if verbose:
            print(f"SymPy Expr1: {sympy_expr1}")
            print(f"SymPy Expr2: {sympy_expr2}")

        # If expressions are equations, compare their RHS
        if isinstance(sympy_expr1, Eq):
            sympy_expr1 = sympy_expr1.rhs
        if isinstance(sympy_expr2, Eq):
            sympy_expr2 = sympy_expr2.rhs

        # Simplify and compare for mathematical equivalence
        sympy_result = simplify(sympy_expr1 - sympy_expr2) == 0
        result_data["sympy_result"] = sympy_result

        # If SymPy fails, delegate to LLM
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
    latex1 = r"R = \\frac{x}{4} \\frac{[2 + (\\alpha_1 + \\alpha_2) \\Delta T]}{(\\alpha_2 - \\alpha_1) \\Delta T}"
    latex2 = r"R = \\frac{x}{2(\\alpha_2 - \\alpha_1) \\Delta T}"
    result = is_equiv(latex1, latex2, verbose=True)
    print(result)

    # Example 2: Expressions with text
    latex3 = r"\\text{Vapor pressure thermometer measures temperatures greater than } 14K"
    latex4 = r"\\text{The temperatures should be greater than 14 kelvin for the vapor pressure thermometer to work}"
    result = is_equiv(latex3, latex4, verbose=True)
    print(result)
