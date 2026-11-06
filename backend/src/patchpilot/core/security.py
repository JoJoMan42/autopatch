from __future__ import annotations

import hashlib
import hmac
import time
from datetime import UTC, datetime, timedelta
from typing import Any

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
from jose import JWTError, jwt
from pydantic import BaseModel

from patchpilot.config import get_settings
from patchpilot.constants import Role
from patchpilot.errors import AuthenticationError, PermissionDeniedError

_hasher = PasswordHasher()
ALGORITHM = "HS256"
DUMMY_HASH = _hasher.hash("patchpilot-timing-equalization-dummy-password")


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class TokenClaims(BaseModel):
    """JWT Token claims model adhering to spec section 2.4."""

    sub: str
    role: Role
    exp: int
    username: str | None = None


# Backward-compatible alias
TokenPayload = TokenClaims


# ---------------------------------------------------------------------------
# Password Hashing (Argon2id per spec section 2.4)
# ---------------------------------------------------------------------------

def hash_password(plain: str) -> str:
    """Hash password using Argon2id with library defaults."""
    return _hasher.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify password against Argon2id hash. Returns False on any error and never raises."""
    try:
        return _hasher.verify(hashed, plain)
    except (VerifyMismatchError, VerificationError, InvalidHashError, ValueError, TypeError):
        return False


def needs_rehash(hashed: str) -> bool:
    """Check if the hash needs to be re-computed with updated parameters."""
    try:
        return _hasher.check_needs_rehash(hashed)
    except (InvalidHashError, ValueError, TypeError):
        return True


def dummy_verify() -> None:
    """Equalize timing for unknown user authentication attempts."""
    try:
        _hasher.verify(DUMMY_HASH, "wrong-password")
    except VerifyMismatchError:
        return


# ---------------------------------------------------------------------------
# JWT Access Tokens
# ---------------------------------------------------------------------------

def create_access_token(
    user_id: str,
    role: Role,
    *,
    username: str | None = None,
    ttl_min: int | None = None,
    expires_delta: timedelta | None = None,
) -> str:
    """Create signed JWT access token with HS256 and expiration."""
    settings = get_settings()

    if expires_delta is not None:
        expire_dt = datetime.now(UTC) + expires_delta
    elif ttl_min is not None:
        expire_dt = datetime.now(UTC) + timedelta(minutes=ttl_min)
    else:
        expire_dt = datetime.now(UTC) + timedelta(minutes=settings.access_token_ttl_min)

    now_ts = int(datetime.now(UTC).timestamp())
    exp_ts = int(expire_dt.timestamp())

    payload: dict[str, Any] = {
        "sub": user_id,
        "role": role.value,
        "iss": "patchpilot",
        "iat": now_ts,
        "exp": exp_ts,
    }
    if username is not None:
        payload["username"] = username

    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str) -> TokenClaims:
    """Decode and validate JWT access token claims. Raises AuthenticationError on failure."""
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[ALGORITHM],
            options={"require_exp": True, "require_sub": True},
        )
        user_id = payload.get("sub")
        role_str = payload.get("role")
        exp_ts = payload.get("exp")
        username = payload.get("username")

        if not user_id or not role_str or not exp_ts:
            raise AuthenticationError("Invalid token claims: missing sub, role, or exp")

        return TokenClaims(
            sub=str(user_id),
            role=Role(role_str),
            exp=int(exp_ts),
            username=str(username) if username else None,
        )
    except (JWTError, ValueError) as err:
        raise AuthenticationError(f"Could not validate token: {err}") from err


# ---------------------------------------------------------------------------
# WebSocket Tickets
# ---------------------------------------------------------------------------

def create_ws_ticket(
    user_id: str,
    job_id: str,
    *,
    redis: Any = None,
) -> str:
    """Create short-lived ticket for WebSocket authentication."""
    settings = get_settings()
    expire_at = int(time.time()) + settings.ws_ticket_ttl_s
    payload = f"{user_id}:{job_id}:{expire_at}"
    signature = hmac.new(
        settings.secret_key.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    ticket = f"{payload}:{signature}"

    if redis is not None:
        try:
            ticket_hash = hashlib.sha256(ticket.encode("utf-8")).hexdigest()
            redis.setex(f"wsticket:{ticket_hash}", settings.ws_ticket_ttl_s, f"{user_id}:{job_id}")
        except (ConnectionError, TimeoutError, OSError):
            return ticket

    return ticket


def verify_ws_ticket(ticket: str, job_id: str) -> str:
    """Verify signed ticket and return user_id if valid."""
    settings = get_settings()
    parts = ticket.split(":")
    if len(parts) != 4:
        raise AuthenticationError("Malformed WebSocket ticket")

    user_id, ticket_job_id, expire_at_str, signature = parts
    if ticket_job_id != job_id:
        raise AuthenticationError("Ticket is not valid for this job")

    try:
        expire_at = int(expire_at_str)
    except ValueError as err:
        raise AuthenticationError("Invalid ticket timestamp") from err

    if time.time() > expire_at:
        raise AuthenticationError("Ticket expired")

    expected_payload = f"{user_id}:{ticket_job_id}:{expire_at_str}"
    expected_sig = hmac.new(
        settings.secret_key.encode("utf-8"),
        expected_payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(signature, expected_sig):
        raise AuthenticationError("Invalid ticket signature")

    return user_id


async def consume_ws_ticket(redis: Any, ticket: str, job_id: str) -> str | None:
    """Consume single-use WebSocket ticket atomically from Redis."""
    if redis is None:
        return verify_ws_ticket(ticket, job_id)

    ticket_hash = hashlib.sha256(ticket.encode("utf-8")).hexdigest()
    key = f"wsticket:{ticket_hash}"

    val = await redis.getdel(key)
    if not val:
        return None

    stored_str = val.decode("utf-8") if isinstance(val, bytes) else str(val)
    parts = stored_str.split(":", 1)
    if len(parts) != 2:
        return None

    stored_user_id, stored_job_id = parts
    if stored_job_id != job_id:
        return None

    return stored_user_id


# ---------------------------------------------------------------------------
# RBAC Authorization
# ---------------------------------------------------------------------------

def check_role(required_roles: list[Role], user_role: Role) -> None:
    """Enforce role requirement."""
    if user_role not in required_roles:
        raise PermissionDeniedError(
            f"Operation requires one of {[r.value for r in required_roles]}, but user has {user_role.value}"
        )
