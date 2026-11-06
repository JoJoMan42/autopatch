from __future__ import annotations

from decimal import Decimal
from typing import Any

from sqlalchemy import Index, Integer, Numeric, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from patchpilot.constants import PatchState, Verdict
from patchpilot.db.base import (
    Base,
    EnumText,
    TimestampMixin,
    enum_check,
    jsonb_type,
    uuid_fk,
    uuid_pk,
)


class PatchCandidateModel(Base, TimestampMixin):
    """One repair attempt for a finding. version is updated only by the state machine."""

    __tablename__ = "patch_candidates"
    __table_args__ = (
        UniqueConstraint("finding_id", "attempt", name="uq_patch_candidates_finding_id_attempt"),
        enum_check("state", PatchState),
        enum_check("verdict", Verdict),
        Index("ix_patch_candidates_finding_id", "finding_id"),
    )

    id: Mapped[str] = uuid_pk()
    finding_id: Mapped[str] = uuid_fk("findings.id")
    job_id: Mapped[str | None] = uuid_fk("jobs.id", nullable=True, use_alter=True)
    attempt: Mapped[int] = mapped_column(Integer, nullable=False)
    model: Mapped[str] = mapped_column(Text, nullable=False)
    provider: Mapped[str] = mapped_column(Text, nullable=False, default="")
    prompt_version: Mapped[str] = mapped_column(Text, nullable=False)
    params: Mapped[dict[str, Any]] = mapped_column(jsonb_type(), nullable=False, default=dict)
    retrieved_chunk_ids: Mapped[list[Any]] = mapped_column(
        jsonb_type(), nullable=False, default=list
    )
    unified_diff: Mapped[str] = mapped_column(Text, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False, default="")
    analysis: Mapped[str] = mapped_column(Text, nullable=False, default="")
    assumptions: Mapped[list[Any]] = mapped_column(jsonb_type(), nullable=False, default=list)
    risks: Mapped[list[Any]] = mapped_column(jsonb_type(), nullable=False, default=list)
    confidence: Mapped[Decimal] = mapped_column(
        Numeric(3, 2), nullable=False, default=Decimal("0.00"), server_default="0"
    )
    risk_score: Mapped[Decimal] = mapped_column(
        Numeric(4, 3), nullable=False, default=Decimal("0.000"), server_default="0"
    )
    judge: Mapped[dict[str, Any] | None] = mapped_column(jsonb_type(), nullable=True)
    generated_test: Mapped[dict[str, Any] | None] = mapped_column(jsonb_type(), nullable=True)
    base_commit: Mapped[str] = mapped_column(Text, nullable=False, default="")
    state: Mapped[PatchState] = mapped_column(
        EnumText(PatchState),
        nullable=False,
        default=PatchState.PROPOSED,
        server_default="proposed",
    )
    verdict: Mapped[Verdict | None] = mapped_column(EnumText(Verdict), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")

    finding: Mapped[FindingModel] = relationship(back_populates="patches", lazy="raise")
    validation_runs: Mapped[list[ValidationRunModel]] = relationship(
        back_populates="patch",
        lazy="raise",
    )
    reviews: Mapped[list[ReviewModel]] = relationship(back_populates="patch", lazy="raise")


from patchpilot.db.models.finding import FindingModel
from patchpilot.db.models.review import ReviewModel
from patchpilot.db.models.validation import ValidationRunModel
