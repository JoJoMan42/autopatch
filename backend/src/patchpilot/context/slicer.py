from __future__ import annotations

import ast
from patchpilot.context.ast_utils import enclosing_function, extract_function_source
from patchpilot.schemas.pipeline import CodeSlice


def slice_code_at_finding(
    file_path: str,
    source: str,
    flagged_line: int,
) -> CodeSlice:
    """Perform intraprocedural backward slicing starting from the flagged line sink."""
    func_node, start_line, end_line = enclosing_function(source, flagged_line)
    enclosing_src = extract_function_source(source, start_line, end_line)

    if func_node is None:
        # Fallback if outside function or unparseable: return lines around flagged_line
        lines = source.splitlines()
        slice_start = max(1, flagged_line - 5)
        slice_end = min(len(lines), flagged_line + 5)
        slice_lines = list(range(slice_start, slice_end + 1))
        return CodeSlice(
            file_path=file_path,
            function_name=None,
            start_line=start_line,
            end_line=end_line,
            source=enclosing_src,
            slice_lines=slice_lines,
            slice_source="\n".join(lines[slice_start - 1 : slice_end]),
            external_params=[],
        )

    # Collect parameter names
    param_names = {arg.arg for arg in func_node.args.args}

    # Step 1: Find sink call at or nearest to flagged line
    tracked_names: set[str] = set()
    sink_lines: set[int] = set()

    for node in ast.walk(func_node):
        if hasattr(node, "lineno") and node.lineno == flagged_line:
            sink_lines.add(node.lineno)
            for subnode in ast.walk(node):
                if isinstance(subnode, ast.Name):
                    tracked_names.add(subnode.id)

    if not tracked_names:
        tracked_names.add("data")
        sink_lines.add(flagged_line)

    # Step 2: Backward traversal of statements in the function body
    included_lines: set[int] = set(sink_lines)
    external_params: set[str] = set()

    # Collect body statements in reverse order
    statements = sorted(
        [stmt for stmt in func_node.body if hasattr(stmt, "lineno")],
        key=lambda s: s.lineno,
        reverse=True,
    )

    for stmt in statements:
        if stmt.lineno > flagged_line:
            continue

        assigned_targets: set[str] = set()
        rhs_names: set[str] = set()

        if isinstance(stmt, ast.Assign):
            for t in stmt.targets:
                for n in ast.walk(t):
                    if isinstance(n, ast.Name):
                        assigned_targets.add(n.id)
            for n in ast.walk(stmt.value):
                if isinstance(n, ast.Name):
                    rhs_names.add(n.id)

        elif isinstance(stmt, (ast.AugAssign, ast.AnnAssign)):
            target = stmt.target
            for n in ast.walk(target):
                if isinstance(n, ast.Name):
                    assigned_targets.add(n.id)
            if stmt.value:
                for n in ast.walk(stmt.value):
                    if isinstance(n, ast.Name):
                        rhs_names.add(n.id)

        # If any target is in our tracked set, include this statement
        if assigned_targets.intersection(tracked_names):
            included_lines.add(stmt.lineno)
            end = getattr(stmt, "end_lineno", stmt.lineno)
            for l in range(stmt.lineno, end + 1):
                included_lines.add(l)
            tracked_names.update(rhs_names)

    # Step 3: Check which tracked names correspond to parameters
    for name in tracked_names:
        if name in param_names:
            external_params.add(name)

    # Step 4: Emit sorted lines and slice source
    sorted_lines = sorted(included_lines)
    all_lines = source.splitlines()
    slice_lines_text = [
        f"{l:4d}: {all_lines[l - 1]}"
        for l in sorted_lines
        if 1 <= l <= len(all_lines)
    ]

    return CodeSlice(
        file_path=file_path,
        function_name=func_node.name,
        start_line=start_line,
        end_line=end_line,
        source=enclosing_src,
        slice_lines=sorted_lines,
        slice_source="\n".join(slice_lines_text),
        external_params=sorted(external_params),
    )

