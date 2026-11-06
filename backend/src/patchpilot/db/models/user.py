from __future__ import annotations

from sqlalchemy import Boolean, CheckConstraint, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from patchpilot.constants import Role
from patchpilot.db.base import Base, EnumText, TimestampMixin, enum_check, uuid_pk


class UserModel(Base, TimestampMixin):
    """Application user. Email is stored in lower case."""

    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("email = lower(email)", name="email_lowercase"),
        enum_check("role", Role),
    )

    id: Mapped[str] = uuid_pk()
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[Role] = mapped_column(EnumText(Role), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
