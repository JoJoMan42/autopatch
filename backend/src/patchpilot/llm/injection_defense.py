from __future__ import annotations

import secrets


def generate_delimiter_token() -> str:
    """Generate a random per-request hex token for prompt isolation boundaries."""
    return secrets.token_hex(4)


def wrap_untrusted(text: str, label: str, token: str | None = None) -> str:
    """Wrap untrusted source code or repository text in unique delimited boundary markers."""
    tok = token or generate_delimiter_token()
    return f"[DATA-{tok}: {label}]\n{text}\n[/DATA-{tok}]"


def check_for_injection_markers(text: str) -> list[str]:
    """Scan untrusted text for adversarial prompt-injection keywords."""
    suspicious_phrases = [
        "ignore previous instructions",
        "system prompt override",
        "disregard all instructions",
        "you are now an unrestricted",
        "do not apply security rules",
        "disable checks",
    ]
    detected = []
    text_lower = text.lower()
    for phrase in suspicious_phrases:
        if phrase in text_lower:
            detected.append(phrase)
    return detected

