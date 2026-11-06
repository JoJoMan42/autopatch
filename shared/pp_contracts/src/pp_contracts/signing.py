from __future__ import annotations

import hashlib
import hmac


def sign_payload(payload: bytes, secret: str) -> str:
    """Compute HMAC-SHA256 hex digest for the payload."""
    secret_bytes = secret.encode("utf-8")
    return hmac.new(secret_bytes, payload, hashlib.sha256).hexdigest()


def verify_signature(payload: bytes, secret: str, expected_signature: str) -> bool:
    """Verify HMAC-SHA256 signature in constant time."""
    actual_signature = sign_payload(payload, secret)
    return hmac.compare_digest(actual_signature, expected_signature)

