from __future__ import annotations

import ast
from pathlib import Path


class ApproximateCallGraph:
    """Intra-project approximate call graph built from AST function and call nodes."""

    def __init__(self) -> None:
        # callee -> set of caller names
        self.callers_map: dict[str, set[str]] = {}
        # caller -> set of callee names
        self.callees_map: dict[str, set[str]] = {}

    def index_source(self, file_path: str, source: str) -> None:
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                caller_name = node.name
                if caller_name not in self.callees_map:
                    self.callees_map[caller_name] = set()

                for subnode in ast.walk(node):
                    if isinstance(subnode, ast.Call):
                        callee_name = None
                        if isinstance(subnode.func, ast.Name):
                            callee_name = subnode.func.id
                        elif isinstance(subnode.func, ast.Attribute):
                            callee_name = subnode.func.attr

                        if callee_name and callee_name != caller_name:
                            self.callees_map[caller_name].add(callee_name)
                            if callee_name not in self.callers_map:
                                self.callers_map[callee_name] = set()
                            self.callers_map[callee_name].add(caller_name)

    def get_callers(self, function_name: str) -> list[str]:
        return sorted(self.callers_map.get(function_name, set()))

    def get_callees(self, function_name: str) -> list[str]:
        return sorted(self.callees_map.get(function_name, set()))

