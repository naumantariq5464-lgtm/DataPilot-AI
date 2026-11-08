"""
Code Validator — Two-layer safety check for AI-generated Python code.

Layer 1: ast.parse() — catches syntax errors without executing.
Layer 2: AST visitor — blocks dangerous imports and function calls.

Implemented fully in Phase 5.
"""

import ast

# Modules that must never appear in AI-generated code
BLOCKED_IMPORTS = {
    "os", "sys", "subprocess", "socket", "shutil",
    "pathlib", "glob", "importlib", "ctypes", "signal",
    "multiprocessing", "threading", "asyncio",
}

# Built-in calls that must never appear
BLOCKED_CALLS = {"exec", "eval", "compile", "__import__", "open"}


class _SafetyVisitor(ast.NodeVisitor):
    """AST visitor that raises ValueError on any blocked pattern."""

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            root = alias.name.split(".")[0]
            if root in BLOCKED_IMPORTS:
                raise ValueError(f"Blocked import: '{alias.name}'")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module:
            root = node.module.split(".")[0]
            if root in BLOCKED_IMPORTS:
                raise ValueError(f"Blocked import: 'from {node.module}'")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        # Direct calls: exec(...), eval(...)
        if isinstance(node.func, ast.Name) and node.func.id in BLOCKED_CALLS:
            raise ValueError(f"Blocked call: '{node.func.id}()'")
        self.generic_visit(node)


def validate_code(code: str) -> None:
    """
    Validates AI-generated Python code.
    Raises ValueError with a descriptive message if unsafe.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        raise ValueError(f"Syntax error in generated code: {e}") from e

    _SafetyVisitor().visit(tree)
