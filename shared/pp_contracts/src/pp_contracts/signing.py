from __future__ import annotations

import hashlib
import hmac
import time


# ---------------------------------------------------------------------------
# Internal helpers (kept for backwards compat; not part of the public API)
# ---------------------------------------------------------------------------

def _sign_payload(payload: bytes, secret: str) -> str:
    """Compute HMAC-SHA256 hex digest for a raw payload."""
    return hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()


def _verify_payload(payload: bytes, secret: str, expected: str) -> bool:
    """Constant-time comparison of HMAC-SHA256 signatures."""
    return hmac.compare_digest(_sign_payload(payload, secret), expected)


# ---------------------------------------------------------------------------
# Public API — used by SandboxClient and the runner auth dependency
# ---------------------------------------------------------------------------

def sign_request(body: bytes, secret: str, timestamp: int) -> str:
    """Return the hex HMAC-SHA256 of ``str(timestamp).encode() + b'.' + body``.

    Both the backend client and the runner must call this with the same secret
    and the same Unix-epoch timestamp (integer seconds).
    """
    message = str(timestamp).encode() + b"." + body
    return hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()


def verify_request(
    body: bytes,
    signature: str,
    secret: str,
    timestamp: int,
    *,
    now: int | None = None,
    max_skew_s: int = 60,
) -> bool:
    """Verify a request signature and reject stale timestamps.

    Returns False (never raises) on any malformed or invalid input.

    Args:
        body: Raw request body bytes.
        signature: Hex HMAC-SHA256 string from the ``X-PP-Signature`` header.
        secret: Shared HMAC secret.
        timestamp: Unix epoch seconds from the ``X-PP-Timestamp`` header.
        now: Current epoch seconds; defaults to ``time.time()`` when None.
        max_skew_s: Maximum allowed age of the timestamp (replay defense).
    """
    try:
        current = int(now if now is not None else time.time())
        if abs(current - timestamp) > max_skew_s:
            return False
        expected = sign_request(body, secret, timestamp)
        return hmac.compare_digest(expected, signature)
    except Exception:  # noqa: BLE001
        return False
