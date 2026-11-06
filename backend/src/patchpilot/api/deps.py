from __future__ import annotations

from typing import Annotated, Callable
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from patchpilot.constants import Role
from patchpilot.core.security import check_role, decode_access_token
from patchpilot.db.session import get_db
from patchpilot.errors import AuthenticationError, PermissionDeniedError
from patchpilot.schemas.auth import TokenPayload


def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
) -> TokenPayload:
    if not authorization or not authorization.startswith("Bearer "):
        # For development / easy testing, allow a default viewer/developer if no auth header
        raise AuthenticationError("Authorization header missing or invalid")

    token = authorization.split(" ")[1]
    return decode_access_token(token)


def require_roles(*allowed_roles: Role) -> Callable[[TokenPayload], TokenPayload]:
    def dependency(
        current_user: Annotated[TokenPayload, Depends(get_current_user)],
    ) -> TokenPayload:
        check_role(list(allowed_roles), current_user.role)
        return current_user

    return dependency

