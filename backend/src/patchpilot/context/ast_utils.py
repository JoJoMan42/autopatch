from __future__ import annotations

import ast
from typing import Any


def enclosing_function(
    source: str, line: int
) -> tuple[ast.FunctionDef | ast.AsyncFunctionDef | None, int, int]:
    """Find the innermost function containing the specified line.
    Returns (node, start_line, end_line) or (None, 1, total_lines).
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None, 1, len(source.splitlines())

    best: ast.FunctionDef | ast.AsyncFunctionDef | None = None
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            start = getattr(node, "lineno", 0)
            end = getattr(node, "end_lineno", start)
            if start <= line <= end:
                if best is None or start >= getattr(best, "lineno", 0):
                    best = node

    if best is not None:
        return best, best.lineno, getattr(best, "end_lineno", best.lineno)

    return None, 1, len(source.splitlines())


def extract_function_source(source: str, start_line: int, end_line: int) -> str:
    """Extract line range (1-indexed inclusive)."""
    lines = source.splitlines()
    start_idx = max(0, start_line - 1)
    end_idx = min(len(lines), end_line)
    return "\n".join(lines[start_idx:end_idx])


def import_list(source: str) -> set[str]:
    """Extract all module root names imported in source."""
    allowed = set()
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return allowed

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                allowed.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                allowed.add(node.module.split(".")[0])

    return allowed


def symbol_table(source: str) -> set[str]:
    """Extract all defined names (functions, classes, variables) in source."""
    symbols = set()
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return symbols

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            symbols.add(node.name)
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            symbols.add(node.id)

    return symbols

