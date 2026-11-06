from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from patchpilot.api.deps import get_current_user
from patchpilot.config import get_settings
from patchpilot.constants import Role
from patchpilot.core.security import (
    create_access_token,
    create_ws_ticket,
    hash_password,
    verify_password,
)
from patchpilot.db.models.user import UserModel
from patchpilot.db.session import get_db
from patchpilot.errors import AuthenticationError, ConflictError
from patchpilot.schemas.auth import (
    LoginRequest,
    Token,
    TokenPayload,
    UserCreate,
    UserResponse,
    WSTicketResponse,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=201)
def register_user(req: UserCreate, db: Session = Depends(get_db)) -> UserModel:
    existing = db.scalar(select(UserModel).where(UserModel.username == req.username))
    if existing:
        raise ConflictError(f"User with username '{req.username}' already exists")

    user = UserModel(
        username=req.username,
        email=req.email,
        hashed_password=hash_password(req.password),
        role=req.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login_user(req: LoginRequest, db: Session = Depends(get_db)) -> Token:
    user = db.scalar(select(UserModel).where(UserModel.username == req.username))
    if not user or not verify_password(req.password, user.hashed_password):
        raise AuthenticationError("Invalid username or password")

    settings = get_settings()
    token_str = create_access_token(user_id=user.id, username=user.username, role=user.role)
    return Token(
        access_token=token_str,
        token_type="bearer",
        expires_in_seconds=settings.access_token_ttl_min * 60,
    )


@router.post("/ws-tickets", response_model=WSTicketResponse)
def get_websocket_ticket(
    job_id: str,
    user: TokenPayload = Depends(get_current_user),
) -> WSTicketResponse:
    settings = get_settings()
    ticket = create_ws_ticket(user_id=user.sub, job_id=job_id)
    return WSTicketResponse(
        ticket=ticket,
        expires_in_seconds=settings.ws_ticket_ttl_s,
    )

