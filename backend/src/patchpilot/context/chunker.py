from __future__ import annotations

import ast
from pydantic import BaseModel


class CodeChunk(BaseModel):
    file_path: str
    symbol: str | None
    start_line: int
    end_line: int
    header: str
    body: str


def chunk_source_file(file_path: str, source: str) -> list[CodeChunk]:
    """Chunk source code using AST for functions and classes, and sliding windows for top-level code."""
    chunks: list[CodeChunk] = []
    lines = source.splitlines()
    total_lines = len(lines)

    try:
        tree = ast.parse(source)
    except SyntaxError:
        # Fallback to sliding window chunking if syntax error exists
        step = 50
        window = 60
        for i in range(0, total_lines, step):
            start = i + 1
            end = min(total_lines, i + window)
            body = "\n".join(lines[start - 1 : end])
            header = f"# File: {file_path} Lines: {start}-{end}"
            chunks.append(
                CodeChunk(
                    file_path=file_path,
                    symbol=None,
                    start_line=start,
                    end_line=end,
                    header=header,
                    body=f"{header}\n{body}",
                )
            )
        return chunks

    handled_lines: set[int] = set()

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            start = getattr(node, "lineno", 1)
            end = getattr(node, "end_lineno", start)
            symbol_kind = "class" if isinstance(node, ast.ClassDef) else "function"
            header = f"# File: {file_path} | {symbol_kind} {node.name} (lines {start}-{end})"
            body = "\n".join(lines[start - 1 : end])
            chunks.append(
                CodeChunk(
                    file_path=file_path,
                    symbol=node.name,
                    start_line=start,
                    end_line=end,
                    header=header,
                    body=f"{header}\n{body}",
                )
            )
            for l in range(start, end + 1):
                handled_lines.add(l)

    # Collect unhandled module-level statements (e.g. imports, global setup)
    unhandled_line_numbers = sorted(set(range(1, total_lines + 1)) - handled_lines)
    if unhandled_line_numbers:
        # Group into blocks
        block_start = unhandled_line_numbers[0]
        prev = block_start
        for l in unhandled_line_numbers[1:]:
            if l != prev + 1:
                body = "\n".join(lines[block_start - 1 : prev])
                header = f"# File: {file_path} | module-level (lines {block_start}-{prev})"
                chunks.append(
                    CodeChunk(
                        file_path=file_path,
                        symbol=None,
                        start_line=block_start,
                        end_line=prev,
                        header=header,
                        body=f"{header}\n{body}",
                    )
                )
                block_start = l
            prev = l
        body = "\n".join(lines[block_start - 1 : prev])
        header = f"# File: {file_path} | module-level (lines {block_start}-{prev})"
        chunks.append(
            CodeChunk(
                file_path=file_path,
                symbol=None,
                start_line=block_start,
                end_line=prev,
                header=header,
                body=f"{header}\n{body}",
            )
        )

    return chunks

