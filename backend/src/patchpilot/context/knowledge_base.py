from __future__ import annotations

from typing import Any

CWE_KNOWLEDGE: dict[str, dict[str, str]] = {
    "CWE-89": {
        "name": "SQL Injection",
        "description": "Untrusted input concatenated or formatted into a database query string.",
        "preferred_fix": "Use parameterized queries with placeholder bindings (?, %s, or :name). Never use string concatenation, format strings, or f-strings for SQL statements.",
        "watch_out": "Dynamic table or column names cannot be parameterized; validate them against a strict allowlist.",
    },
    "CWE-78": {
        "name": "OS Command Injection",
        "description": "Untrusted input passed to a command shell execution function such as os.system or subprocess with shell=True.",
        "preferred_fix": "Use subprocess.run with a list of discrete arguments, never a single string. Set shell=False explicitly.",
        "watch_out": "Beware of argument injection: user-controlled values starting with a dash (-) can alter tool flags. Validate inputs or prefix with '--'.",
    },
    "CWE-22": {
        "name": "Path Traversal",
        "description": "User input joined to a filesystem directory without verifying that the resolved path stays within the base directory.",
        "preferred_fix": "Resolve the absolute canonical path (e.g., os.path.realpath or Path.resolve) and assert that it starts with the canonical base directory prefix.",
        "watch_out": "Watch for symbolic links and time-of-check-to-time-of-use (TOCTOU) file race conditions.",
    },
    "CWE-79": {
        "name": "Cross-Site Scripting (XSS)",
        "description": "Untrusted input rendered in HTML or template output without context-aware escaping.",
        "preferred_fix": "Enable template engine auto-escaping (e.g. Jinja2 autoescape=True or select_autoescape). Use markupsafe.escape for raw interpolation.",
        "watch_out": "Avoid misusing '| safe' or Markup() filters on untrusted user data.",
    },
    "CWE-798": {
        "name": "Use of Hard-coded Credentials",
        "description": "Sensitive credentials, passwords, or secret tokens hard-coded directly in source code.",
        "preferred_fix": "Read credentials from environment variables (e.g., os.environ.get('SECRET_KEY')) or an external secrets vault.",
        "watch_out": "Changing source code does not revoke the compromised secret. The leaked credential must be rotated immediately.",
    },
    "CWE-327": {
        "name": "Use of Broken or Risky Cryptographic Algorithm",
        "description": "Obsolete or weak hash/encryption algorithms (such as MD5, SHA-1, DES) used for security-sensitive operations.",
        "preferred_fix": "For passwords, use Argon2id, bcrypt, or scrypt. For cryptographic signatures and integrity, use SHA-256 or SHA-512.",
        "watch_out": "Existing stored hashes will require a migration strategy when changing password hashing algorithms.",
    },
    "CWE-502": {
        "name": "Deserialization of Untrusted Data",
        "description": "Loading untrusted binary objects or serialized payloads using pickle, marshal, or unsafe yaml.load.",
        "preferred_fix": "Use safe serialization formats such as JSON (json.loads) or yaml.safe_load.",
        "watch_out": "Switching data formats may affect backwards compatibility with older clients.",
    },
}


def get_cwe_guidance(cwe: str | None) -> str:
    """Retrieve curated secure-coding guidance for the given CWE."""
    if not cwe:
        return "Apply least-privilege, validate all external inputs, and ensure deterministic type checking."

    norm_cwe = cwe.upper().strip()
    if not norm_cwe.startswith("CWE-") and norm_cwe.isdigit():
        norm_cwe = f"CWE-{norm_cwe}"

    info = CWE_KNOWLEDGE.get(norm_cwe)
    if not info:
        return f"Review OWASP guidelines for {norm_cwe}. Ensure input validation and sanitize data before output."

    return (
        f"CWE: {norm_cwe} ({info['name']})\n"
        f"Description: {info['description']}\n"
        f"Preferred Fix: {info['preferred_fix']}\n"
        f"Watch Out: {info['watch_out']}"
    )

