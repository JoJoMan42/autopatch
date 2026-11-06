from patchpilot.context.ast_utils import enclosing_function, import_list, symbol_table
from patchpilot.context.slicer import slice_code_at_finding

SAMPLE_CODE = """import os
import sqlite3

def helper():
    return 42

def find_user(name: str):
    raw_query = "SELECT * FROM users WHERE " + name
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    cursor.execute(raw_query)
    return cursor.fetchall()
"""


def test_enclosing_function_finds_correct_function():
    node, start, end = enclosing_function(SAMPLE_CODE, line=11)
    assert node is not None
    assert node.name == "find_user"
    assert start == 7


def test_import_list():
    imports = import_list(SAMPLE_CODE)
    assert "os" in imports
    assert "sqlite3" in imports


def test_symbol_table():
    symbols = symbol_table(SAMPLE_CODE)
    assert "helper" in symbols
    assert "find_user" in symbols


def test_slicer_extracts_backward_slice():
    slice_result = slice_code_at_finding(
        file_path="shop/db.py",
        source=SAMPLE_CODE,
        flagged_line=11,  # cursor.execute(raw_query)
    )
    assert slice_result.function_name == "find_user"
    assert "name" in slice_result.external_params
    assert 8 in slice_result.slice_lines  # raw_query definition
    assert 11 in slice_result.slice_lines  # cursor.execute

