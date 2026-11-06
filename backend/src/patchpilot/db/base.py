from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from sqlalchemy import (
    JSON,
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    MetaData,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import TypeDecorator, Uuid

NAMING_CONVENTION: dict[str, str] = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Declarative base. Constraint names stay stable for Alembic."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)


def new_id() -> str:
    """Return a new UUID string."""
    return str(uuid.uuid4())


def utcnow() -> datetime:
    """Return the current timezone-aware UTC time."""
    return datetime.now(UTC)


def enum_check(column: str, enum_cls: type[Enum]) -> CheckConstraint:
    """Build a CHECK constraint limiting a text column to an enum's values."""
    values = ", ".join(f"'{member.value}'" for member in enum_cls)
    return CheckConstraint(f'"{column}" IN ({values})', name=f"{column}_enum")


def jsonb_type() -> JSON:
    """JSONB on PostgreSQL and JSON on SQLite (unit tests)."""
    return JSONB().with_variant(JSON(), "sqlite")


def uuid_pk() -> Any:
    """UUID string primary key. The server default is gen_random_uuid()."""
    return mapped_column(
        Uuid(as_uuid=False),
        primary_key=True,
        default=new_id,
        server_default=text("gen_random_uuid()"),
    )


def uuid_fk(target: str, *, nullable: bool = False, use_alter: bool = False) -> Any:
    """UUID foreign key with ON DELETE RESTRICT."""
    return mapped_column(
        Uuid(as_uuid=False),
        ForeignKey(target, ondelete="RESTRICT", use_alter=use_alter),
        nullable=nullable,
    )


def bigserial_pk() -> Any:
    """Bigserial primary key. SQLite uses INTEGER so inserts autoincrement."""
    return mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )


class EnumText(TypeDecorator[str]):
    """Store an enum as TEXT and return the enum member in Python."""

    impl = Text
    cache_ok = False

    def __init__(self, enum_cls: type[Enum]) -> None:
        super().__init__()
        self.enum_cls = enum_cls

    def process_bind_param(self, value: Any, dialect: Any) -> str | None:
        """Persist the enum value."""
        if value is None:
            return None
        if isinstance(value, self.enum_cls):
            return str(value.value)
        return str(value)

    def process_result_value(self, value: Any, dialect: Any) -> Enum | None:
        """Rehydrate the enum member."""
        if value is None:
            return None
        return self.enum_cls(value)


class TimestampMixin:
    """created_at column for tables that record insertion time."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        server_default=func.now(),
    )
