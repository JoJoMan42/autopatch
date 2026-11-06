from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import CHAR, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column

from patchpilot.db.base import Base, bigserial_pk, jsonb_type, utcnow


class AuditEventModel(Base):
    """Hash-chained audit row. The table is append-only in PostgreSQL."""

    __tablename__ = "audit_events"

    id: Mapped[int] = bigserial_pk()
    ts: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        server_default="now()",
    )
    actor: Mapped[str] = mapped_column(Text, nullable=False)
    action: Mapped[str] = mapped_column(Text, nullable=False)
    entity_type: Mapped[str] = mapped_column(Text, nullable=False)
    entity_id: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(jsonb_type(), nullable=False, default=dict)
    prev_hash: Mapped[str] = mapped_column(CHAR(64), nullable=False)
    hash: Mapped[str] = mapped_column(CHAR(64), unique=True, nullable=False)
