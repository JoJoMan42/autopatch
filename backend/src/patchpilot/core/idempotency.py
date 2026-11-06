from __future__ import annotations

import time
from typing import Any

# Simple local cache for idempotency keys if Redis is not connected
_IDEMPOTENCY_CACHE: dict[str, tuple[float, Any]] = {}
CACHE_TTL_SECONDS = 300


def check_idempotency_key(key: str) -> Any | None:
    now = time.time()
    if key in _IDEMPOTENCY_CACHE:
        expires_at, response_data = _IDEMPOTENCY_CACHE[key]
        if now < expires_at:
            return response_data
        del _IDEMPOTENCY_CACHE[key]
    return None


def store_idempotency_key(key: str, response_data: Any, ttl: int = CACHE_TTL_SECONDS) -> None:
    _IDEMPOTENCY_CACHE[key] = (time.time() + ttl, response_data)

