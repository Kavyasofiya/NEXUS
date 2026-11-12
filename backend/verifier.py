
import ast
import re


def extract_python_code(response):
    """Extract Python code from an AI response."""

    match = re.search(
        r"```(?:python)?\s*(.*?)```",
        response,
        re.IGNORECASE | re.DOTALL
    )

    if match:
        return match.group(1).strip()

    return response.strip()


def verify_code(response):
    """Extract code and check whether its Python syntax is valid."""

    code = extract_python_code(response)

    if not code:
        return {
            "verified": False,
            "message": "No code was provided."
        }

    try:
        ast.parse(code)

        return {
            "verified": True,
            "message": "Python syntax is valid.",
            "code": code
        }

    except SyntaxError as error:
        return {
            "verified": False,
            "message": f"Syntax error: {error}",
            "code": code
        }
