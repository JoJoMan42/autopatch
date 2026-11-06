from __future__ import annotations

import hmac
import time
from datetime import datetime, timedelta, timezone
from typing import Any
from jose import JWTError, jwt
from passlib.context import CryptContext

from patchpilot.config import get_settings
from patchpilot.constants import Role
from patchpilot.errors import AuthenticationError, PermissionDeniedError
from patchpilot.schemas.auth import TokenPayload

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    user_id: str,
    username: str,
    role: Role,
    expires_delta: timedelta | None = None,
) -> str:
    settings = get_settings()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.access_token_ttl_min)
    )
    to_encode = {
        "sub": user_id,
        "username": username,
        "role": role.value,
        "exp": expire,
    }
    return jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str) -> TokenPayload:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        username = payload.get("username")
        role_str = payload.get("role")
        exp_timestamp = payload.get("exp")

        if not user_id or not username or not role_str or not exp_timestamp:
            raise AuthenticationError("Invalid token claims")

        return TokenPayload(
            sub=user_id,
            username=username,
            role=Role(role_str),
            exp=datetime.fromtimestamp(exp_timestamp, tz=timezone.utc),
        )
    except (JWTError, ValueError) as err:
        raise AuthenticationError(f"Could not validate token: {err}") from err


def create_ws_ticket(user_id: str, job_id: str) -> str:
    """Create short-lived signed ticket for WebSocket authentication."""
    settings = get_settings()
    expire_at = int(time.time()) + settings.ws_ticket_ttl_s
    payload = f"{user_id}:{job_id}:{expire_at}"
    signature = hmac.new(
        settings.secret_key.encode("utf-8"), payload.encode("utf-8"), "sha256"
    ).hexdigest()
    return f"{payload}:{signature}"


def verify_ws_ticket(ticket: str, job_id: str) -> str:
    """Verify ticket and return user_id if valid."""
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
        "sha256",
    ).hexdigest()

    if not hmac.compare_digest(signature, expected_sig):
        raise AuthenticationError("Invalid ticket signature")

    return user_id


def check_role(required_roles: list[Role], user_role: Role) -> None:
    """Enforce role requirement."""
    if user_role not in required_roles:
        raise PermissionDeniedError(
            f"Operation requires one of {[r.value for r in required_roles]}, but user has {user_role.value}"
        )

