from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel
from patchpilot.constants import Role


class LoginRequest(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_seconds: int


class TokenPayload(BaseModel):
    sub: str  # user id
    username: str
    role: Role
    exp: datetime


class WSTicketResponse(BaseModel):
    ticket: str
    expires_in_seconds: int


class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    role: Role = Role.DEVELOPER


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    role: Role
    created_at: datetime
