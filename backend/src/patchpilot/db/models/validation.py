from __future__ import annotations

from typing import Any

from sqlalchemy import Index, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from patchpilot.constants import StageName, StageOutcome
from patchpilot.db.base import (
    Base,
    EnumText,
    TimestampMixin,
    enum_check,
    jsonb_type,
    uuid_fk,
    uuid_pk,
)


class ValidationRunModel(Base, TimestampMixin):
    """One validation stage result. The table is append-only in PostgreSQL."""

    __tablename__ = "validation_runs"
    __table_args__ = (
        enum_check("stage", StageName),
        enum_check("outcome", StageOutcome),
        Index("ix_validation_runs_patch_id_stage", "patch_id", "stage"),
    )

    id: Mapped[str] = uuid_pk()
    patch_id: Mapped[str] = uuid_fk("patch_candidates.id")
    stage: Mapped[StageName] = mapped_column(EnumText(StageName), nullable=False)
    outcome: Mapped[StageOutcome] = mapped_column(EnumText(StageOutcome), nullable=False)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    log_uri: Mapped[str] = mapped_column(Text, nullable=False, default="")
    details: Mapped[dict[str, Any]] = mapped_column(jsonb_type(), nullable=False, default=dict)

    patch: Mapped[PatchCandidateModel] = relationship(
        back_populates="validation_runs",
        lazy="raise",
    )


from patchpilot.db.models.patch import PatchCandidateModel
