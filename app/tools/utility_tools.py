import ast
import operator
from datetime import datetime


ALLOWED_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow
}


def _evaluate_math_node(node):
    if isinstance(node, ast.Expression):
        return _evaluate_math_node(node.body)

    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value

    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        value = _evaluate_math_node(node.operand)
        return value if isinstance(node.op, ast.UAdd) else -value

    if isinstance(node, ast.BinOp):
        operator_func = ALLOWED_OPERATORS.get(type(node.op))
        if operator_func is None:
            raise ValueError("Unsupported operator")

        left = _evaluate_math_node(node.left)
        right = _evaluate_math_node(node.right)

        if isinstance(node.op, ast.Pow) and abs(right) > 8:
            raise ValueError("Exponent is too large")

        result = operator_func(left, right)
        if abs(result) > 1_000_000_000:
            raise ValueError("Result is too large")

        return result

    raise ValueError("Unsupported expression")


def build_utility_tools():
    from langchain.tools import tool

    @tool
    def get_current_datetime() -> str:
        """Get the current local date and time."""
        return datetime.now().astimezone().strftime(
            "%A, %d %B %Y, %I:%M %p %Z"
        )

    @tool
    def calculate(expression: str) -> str:
        """Calculate a simple arithmetic expression using numbers and operators."""
        cleaned_expression = expression.strip()
        if len(cleaned_expression) > 120:
            return "The expression is too long."

        try:
            parsed = ast.parse(
                cleaned_expression,
                mode="eval"
            )
            result = _evaluate_math_node(parsed)
        except Exception as exc:
            return f"Calculation failed: {exc}"

        return f"{cleaned_expression} = {result:g}"

    return [
        get_current_datetime,
        calculate
    ]
