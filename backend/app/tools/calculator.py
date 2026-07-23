\"\"\"
Calculator Tool
Safely evaluates mathematical expressions.
\"\"\"
import ast
import operator
import math
from app.utils.logger import logger

# Supported math operators/functions
_OP_MAP = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: lambda x: x,
}

_FN_MAP = {
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "sqrt": math.sqrt,
    "log": math.log,
    "log10": math.log10,
    "exp": math.exp,
    "abs": abs,
    "pi": math.pi,
    "e": math.e,
}

class SafeEvaluator:
    def eval(self, expr_str: str):
        try:
            # Clean expression string
            clean_str = expr_str.strip().replace("^", "**")
            node = ast.parse(clean_str, mode="eval")
            return self._eval(node.body)
        except Exception as e:
            logger.warning("calculator_eval_failed", expr=expr_str, error=str(e))
            raise ValueError(f"Invalid math expression: {str(e)}")

    def _eval(self, node):
        if isinstance(node, ast.Num):
            return node.n
        elif isinstance(node, ast.Constant): # Python 3.8+
            return node.value
        elif isinstance(node, ast.BinOp):
            left = self._eval(node.left)
            right = self._eval(node.right)
            op = type(node.op)
            if op in _OP_MAP:
                return _OP_MAP[op](left, right)
            raise TypeError(f"Unsupported binary operator: {op.__name__}")
        elif isinstance(node, ast.UnaryOp):
            operand = self._eval(node.operand)
            op = type(node.op)
            if op in _OP_MAP:
                return _OP_MAP[op](operand)
            raise TypeError(f"Unsupported unary operator: {op.__name__}")
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in _FN_MAP:
                args = [self._eval(arg) for arg in node.args]
                return _FN_MAP[node.func.id](*args)
            raise TypeError(f"Unsupported function call")
        elif isinstance(node, ast.Name):
            if node.id in _FN_MAP:
                return _FN_MAP[node.id]
            raise NameError(f"Unsupported variable: {node.id}")
        else:
            raise TypeError(f"Unsupported syntax node: {type(node).__name__}")


def calculate(expression: str) -> str:
    \"\"\"Safe evaluation of mathematical expression.\"\"\"
    evaluator = SafeEvaluator()
    try:
        res = evaluator.eval(expression)
        return f"Result of '{expression}' is: {res}"
    except Exception as e:
        return f"Error: Could not evaluate '{expression}'. {str(e)}"
