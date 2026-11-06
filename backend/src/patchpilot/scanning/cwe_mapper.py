from __future__ import annotations

RULE_TO_CWE: dict[str, str] = {
    # SQL Injection
    "B608": "CWE-89",
    "python.sqlalchemy.security.injection": "CWE-89",
    "python.django.security.injection.sql": "CWE-89",
    # OS Command Injection
    "B602": "CWE-78",
    "B605": "CWE-78",
    "B607": "CWE-78",
    "python.lang.security.deserialization.pickle": "CWE-502",
    # Path Traversal
    "B374": "CWE-22",
    "python.lang.security.audit.path-traversal": "CWE-22",
    # XSS
    "python.jinja2.security.audit.autoescape": "CWE-79",
    "B701": "CWE-79",
    # Hard-coded Credentials
    "B105": "CWE-798",
    "B106": "CWE-798",
    "B107": "CWE-798",
    "generic.secrets.security.detected": "CWE-798",
    # Weak Cryptography
    "B303": "CWE-327",
    "B304": "CWE-327",
    "B305": "CWE-327",
    "B324": "CWE-327",
    # Unsafe Deserialization
    "B301": "CWE-502",
    "B403": "CWE-502",
    "B506": "CWE-502",
}


def map_rule_to_cwe(rule_id: str, reported_cwe: str | None = None) -> str | None:
    """Normalize and map scanner-specific rule IDs or reported CWE strings into canonical CWE-XXX."""
    if reported_cwe:
        cleaned = reported_cwe.upper().strip()
        if not cleaned.startswith("CWE-") and cleaned.isdigit():
            return f"CWE-{cleaned}"
        if cleaned.startswith("CWE-"):
            return cleaned

    for pattern, cwe in RULE_TO_CWE.items():
        if pattern.lower() in rule_id.lower():
            return cwe

    return None

