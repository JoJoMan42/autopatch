from __future__ import annotations

from decimal import Decimal
from typing import Any

from sqlalchemy import (
    CHAR,
    CheckConstraint,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from patchpilot.db.base import Base, TimestampMixin, jsonb_type, uuid_fk, uuid_pk


class LLMCallModel(Base, TimestampMixin):
    """One model invocation: tokens, latency, and artifact URIs."""

    __tablename__ = "llm_calls"
    __table_args__ = (
        CheckConstraint("status IN ('ok', 'error')", name="status_values"),
    )

    id: Mapped[str] = uuid_pk()
    job_id: Mapped[str | None] = uuid_fk("jobs.id", nullable=True)
    patch_id: Mapped[str | None] = uuid_fk("patch_candidates.id", nullable=True)
    purpose: Mapped[str] = mapped_column(Text, nullable=False)
    provider: Mapped[str] = mapped_column(Text, nullable=False)
    model: Mapped[str] = mapped_column(Text, nullable=False)
    prompt_version: Mapped[str] = mapped_column(Text, nullable=False)
    params: Mapped[dict[str, Any]] = mapped_column(jsonb_type(), nullable=False, default=dict)
    prompt_hash: Mapped[str] = mapped_column(CHAR(64), nullable=False)
    prompt_uri: Mapped[str | None] = mapped_column(Text, nullable=True)
    response_uri: Mapped[str | None] = mapped_column(Text, nullable=True)
    tokens_in: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    tokens_out: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cost_usd: Mapped[Decimal] = mapped_column(
        Numeric(10, 6), nullable=False, default=Decimal(0), server_default="0"
    )
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="ok", server_default="ok")
    error: Mapped[str | None] = mapped_column(Text, nullable=True)


class PromptTemplate(Base, TimestampMixin):
    """Versioned prompt template stored in the prompts table."""

    __tablename__ = "prompts"
    __table_args__ = (UniqueConstraint("name", "version", name="uq_prompts_name_version"),)

    id: Mapped[str] = uuid_pk()
    name: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[str] = mapped_column(Text, nullable=False)
    sha256: Mapped[str] = mapped_column(CHAR(64), nullable=False)
    template: Mapped[str] = mapped_column(Text, nullable=False)
