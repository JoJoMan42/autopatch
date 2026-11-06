from __future__ import annotations

import re

# Redaction patterns for common sensitive tokens
REDACTION_PATTERNS = [
    # API Keys / Bearer tokens
    (re.compile(r"(sk-[a-zA-Z0-9_-]{20,})"), "[REDACTED_API_KEY]"),
    (re.compile(r"(Bearer\s+[a-zA-Z0-9_\-\.]{20,})", re.IGNORECASE), "Bearer [REDACTED_TOKEN]"),
    # DB connection password: postgres://user:pass@host
    (re.compile(r"(://[^:]+:)([^@]+)(@)"), r"\1[REDACTED_PASSWORD]\3"),
    # Generic password assignments: password = "..." or password: "..."
    (
        re.compile(r"((?:password|secret|api_key|token)\s*[:=]\s*['\"])([^'\"]+)(['\"])", re.IGNORECASE),
        r"\1[REDACTED]\3",
    ),
]


def redact_sensitive_text(text: str) -> str:
    """Mask known secret patterns from the provided text string."""
    if not text:
        return text
    sanitized = text
    for pattern, replacement in REDACTION_PATTERNS:
        sanitized = pattern.sub(replacement, sanitized)
    return sanitized

