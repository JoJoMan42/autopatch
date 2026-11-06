from __future__ import annotations

import ast
import sys
from patchpilot.schemas.pipeline import GuardIssue

BANNED_CALLS = {"eval", "exec", "compile", "__import__"}

# Standard library module names in Python 3.10+
STDLIB_MODULES = getattr(sys, "stdlib_module_names", set())


def check_ast_guard(
    patched_source: str,
    file_path: str,
    project_allowed_imports: set[str] | None = None,
) -> list[GuardIssue]:
    """Parse patched source into AST and enforce syntactic and structural security rules."""
    issues: list[GuardIssue] = []

    try:
        tree = ast.parse(patched_source)
    except SyntaxError as e:
        return [
            GuardIssue(
                code="SYNTAX_ERROR",
                message=f"Syntax error: {e.msg} at line {e.lineno}",
                file_path=file_path,
                line=e.lineno,
            )
        ]

    effective_allowed = set(STDLIB_MODULES)
    if project_allowed_imports:
        effective_allowed.update(project_allowed_imports)

    for node in ast.walk(tree):
        # 1. Check for banned imports
        imported_roots: list[str] = []
        if isinstance(node, ast.Import):
            imported_roots = [alias.name.split(".")[0] for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported_roots = [node.module.split(".")[0]]

        for mod in imported_roots:
            if mod and mod not in effective_allowed:
                issues.append(
                    GuardIssue(
                        code="IMPORT_NOT_ALLOWED",
                        message=f"Disallowed or phantom package import detected: '{mod}'",
                        file_path=file_path,
                        line=getattr(node, "lineno", None),
                    )
                )

        # 2. Check for banned dangerous function calls
        if isinstance(node, ast.Call):
            call_name = None
            if isinstance(node.func, ast.Name):
                call_name = node.func.id
            if call_name and call_name in BANNED_CALLS:
                issues.append(
                    GuardIssue(
                        code="BANNED_CALL",
                        message=f"Dangerous function invocation banned by security policy: '{call_name}()'",
                        file_path=file_path,
                        line=getattr(node, "lineno", None),
                    )
                )

    return issues

