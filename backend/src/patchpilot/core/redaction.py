from __future__ import annotations

import re
from typing import Any

# ---------------------------------------------------------------------------
# Redaction patterns for sensitive tokens and secrets
# ---------------------------------------------------------------------------

SECRET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    # Private key blocks
    (
        "private_key",
        re.compile(
            r"-----BEGIN [A-Z ]+PRIVATE KEY-----[\s\S]*?-----END [A-Z ]+PRIVATE KEY-----"
        ),
    ),
    # JWT-shaped strings (3 base64url segments separated by dots)
    (
        "jwt",
        re.compile(r"\beyJ[a-zA-Z0-9_-]{10,}\.eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}\b"),
    ),
    # API Keys / Bearer tokens
    ("api_key", re.compile(r"\bsk-[a-zA-Z0-9_-]{20,}\b")),
    (
        "bearer_token",
        re.compile(r"(Bearer\s+)[a-zA-Z0-9_\-\.]{20,}", re.IGNORECASE),
    ),
    # DB connection credentials: postgres://user:pass@host
    (
        "db_password",
        re.compile(r"(://[^:\s]+:)([^@\s]+)(@)"),
    ),
    # Generic password / secret / token assignments: password = "..."
    (
        "assignment",
        re.compile(
            r"((?:password|secret|api_key|token)\s*[:=]\s*['\"])([^'\"]+)(['\"])",
            re.IGNORECASE,
        ),
    ),
    # Quoted high-entropy hex or base64 strings (>= 32 chars)
    (
        "high_entropy",
        re.compile(r"(['\"])([0-9a-fA-F]{32,}|[A-Za-z0-9+/=]{40,})\1"),
    ),
]

# ANSI escape sequence stripper
ANSI_ESCAPE_PATTERN: re.Pattern[str] = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

# Control character stripper (keeps \t, \n, \r)
CONTROL_CHAR_PATTERN: re.Pattern[str] = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]")


def strip_control_chars(text: str) -> str:
    """Remove ANSI escape sequences and non-printable control characters, preserving \t, \n, \r."""
    if not text:
        return text
    without_ansi = ANSI_ESCAPE_PATTERN.sub("", text)
    return CONTROL_CHAR_PATTERN.sub("", without_ansi)


def redact_secrets(text: str) -> str:
    """Mask known secret patterns from the provided text string. Pure and idempotent."""
    if not text:
        return text

    sanitized = text
    for kind, pattern in SECRET_PATTERNS:
        if kind == "api_key":
            sanitized = pattern.sub("[REDACTED_API_KEY]", sanitized)
        elif kind == "bearer_token":
            sanitized = pattern.sub(r"\1[REDACTED_TOKEN]", sanitized)
        elif kind == "db_password":
            sanitized = pattern.sub(r"\1[REDACTED_PASSWORD]\3", sanitized)
        elif kind == "assignment":
            sanitized = pattern.sub(r"\1[REDACTED]\3", sanitized)
        elif kind == "high_entropy":
            sanitized = pattern.sub(r"\1[REDACTED:high_entropy]\1", sanitized)
        else:
            sanitized = pattern.sub(f"[REDACTED:{kind}]", sanitized)

    return sanitized


# Backward-compatible alias for existing callers
redact_sensitive_text = redact_secrets


def redact_mapping(obj: Any) -> Any:
    """Recursively redact secrets in nested dictionaries, lists, or primitive values."""
    if isinstance(obj, str):
        return redact_secrets(obj)
    if isinstance(obj, dict):
        return {k: redact_mapping(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [redact_mapping(item) for item in obj]
    if isinstance(obj, tuple):
        return tuple(redact_mapping(item) for item in obj)
    return obj


def sanitize_for_prompt(text: str, max_chars: int = 4000) -> str:
    """Strip control characters, redact secrets, and truncate to max_chars preserving head & tail."""
    clean = strip_control_chars(text)
    redacted = redact_secrets(clean)

    if len(redacted) <= max_chars:
        return redacted

    marker = "\n[... truncated ...]\n"
    avail = max(0, max_chars - len(marker))
    half = avail // 2
    return redacted[:half] + marker + redacted[-half:]
