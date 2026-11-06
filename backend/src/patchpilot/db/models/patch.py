from __future__ import annotations

import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from patchpilot.constants import PatchState
from patchpilot.db.base import Base


class PatchCandidateModel(Base):
    __tablename__ = "patch_candidates"
    __table_args__ = (
        UniqueConstraint("finding_id", "attempt", name="uq_finding_attempt"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    finding_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("findings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    attempt: Mapped[int] = mapped_column(Integer, nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(50), nullable=False)
    unified_diff: Mapped[str] = mapped_column(Text, nullable=False)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    state: Mapped[PatchState] = mapped_column(
        Enum(PatchState), default=PatchState.PROPOSED, nullable=False, index=True
    )
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    finding: Mapped[FindingModel] = relationship("FindingModel", back_populates="patches")
    validation_runs: Mapped[list[ValidationRunModel]] = relationship(
        "ValidationRunModel", back_populates="patch"
    )
    reviews: Mapped[list[ReviewModel]] = relationship("ReviewModel", back_populates="patch")


from patchpilot.db.models.finding import FindingModel  # noqa: E402
from patchpilot.db.models.validation import ValidationRunModel  # noqa: E402
from patchpilot.db.models.review import ReviewModel  # noqa: E402

