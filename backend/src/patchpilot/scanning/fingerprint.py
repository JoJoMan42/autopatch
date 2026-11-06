from __future__ import annotations

import hashlib
import re


def generate_finding_fingerprint(
    file_path: str,
    rule_id: str,
    code_context: str | None = None,
) -> str:
    """Generate a stable finding fingerprint resilient to minor whitespace shifts."""
    norm_path = file_path.replace("\\", "/").strip().lower()
    norm_context = re.sub(r"\s+", " ", code_context or "").strip()
    raw = f"{norm_path}:{rule_id.strip()}:{norm_context}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

