from __future__ import annotations

import sqlite3
from typing import Any


class DatabaseClient:
    def __init__(self, db_path: str = ":memory:") -> None:
        self.conn = sqlite3.connect(db_path)
        self._init_schema()

    def _init_schema(self) -> None:
        with self.conn:
            self.conn.execute(
                "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, email TEXT)"
            )
            self.conn.execute(
                "INSERT INTO users (name, email) VALUES ('alice', 'alice@example.com')"
            )

    def find_user_by_name(self, name: str) -> list[Any]:
        # VULNERABLE TO CWE-89 (SQL Injection) via string formatting
        cursor = self.conn.cursor()
        query = f"SELECT * FROM users WHERE name = '{name}'"
        cursor.execute(query)
        return cursor.fetchall()

    def find_user_safely(self, name: str) -> list[Any]:
        # Parameterized query (safe)
        cursor = self.conn.cursor()
        query = "SELECT * FROM users WHERE name = ?"
        cursor.execute(query, (name,))
        return cursor.fetchall()

