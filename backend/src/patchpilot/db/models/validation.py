from __future__ import annotations

import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from patchpilot.constants import StageName, StageOutcome
from patchpilot.db.base import Base


class ValidationRunModel(Base):
    __tablename__ = "validation_runs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    patch_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("patch_candidates.id", ondelete="CASCADE"), nullable=False, index=True
    )
    stage: Mapped[StageName] = mapped_column(Enum(StageName), nullable=False)
    outcome: Mapped[StageOutcome] = mapped_column(Enum(StageOutcome), nullable=False)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    log_uri: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    patch: Mapped[PatchCandidateModel] = relationship(
        "PatchCandidateModel", back_populates="validation_runs"
    )


from patchpilot.db.models.patch import PatchCandidateModel  # noqa: E402

