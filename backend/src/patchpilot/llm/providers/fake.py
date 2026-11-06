from __future__ import annotations

import json
import time
from patchpilot.llm.providers.base import BaseLLMProvider
from patchpilot.llm.types import LLMRequest, LLMResponse


class FakeLLMProvider(BaseLLMProvider):
    """Deterministic offline LLM provider for unit tests and local demonstrations."""

    @property
    def provider_name(self) -> str:
        return "fake"

    def complete(self, request: LLMRequest) -> LLMResponse:
        start_time = time.perf_counter()
        user_msg = next((m.content for m in request.messages if m.role == "user"), "")

        # Default synthetic patch for CWE-89 SQL injection
        if "CWE-89" in user_msg or "B608" in user_msg:
            resp_payload = {
                "status": "fixed",
                "analysis": "SQL query was dynamically constructed via string concatenation in cursor.execute.",
                "diff": """--- a/shop/db.py\n+++ b/shop/db.py\n@@ -40,3 +40,3 @@\n-    query = f"SELECT * FROM users WHERE name = '{name}'"\n-    cursor.execute(query)\n+    query = "SELECT * FROM users WHERE name = %s"\n+    cursor.execute(query, (name,))""",
                "explanation": "Replaced f-string SQL query concatenation with parameterized query placeholder and bound tuple argument.",
                "assumptions": ["Database driver supports standard tuple parameter binding."],
                "risks": ["None; parameterized binding is the standard secure pattern."],
                "confidence": 0.95,
            }
        elif "CWE-78" in user_msg or "B602" in user_msg:
            resp_payload = {
                "status": "fixed",
                "analysis": "Arbitrary command execution via shell=True parameter.",
                "diff": """--- a/shop/exec_tools.py\n+++ b/shop/exec_tools.py\n@@ -12,3 +12,3 @@\n-    subprocess.run(f"cat {filename}", shell=True)\n+    subprocess.run(["cat", filename], shell=False, check=True)""",
                "explanation": "Passes executable and arguments as an isolated list with shell=False.",
                "assumptions": ["Command binary exists in system PATH."],
                "risks": ["None."],
                "confidence": 0.92,
            }
        else:
            resp_payload = {
                "status": "cannot_fix",
                "reason": "Vulnerability requires manual structural refactoring.",
            }

        text = json.dumps(resp_payload, indent=2)
        latency = int((time.perf_counter() - start_time) * 1000)

        return LLMResponse(
            text=text,
            model=request.model or "fake-model",
            provider=self.provider_name,
            tokens_in=len(user_msg) // 4,
            tokens_out=len(text) // 4,
            latency_ms=latency,
            finish_reason="stop",
        )

