from __future__ import annotations

import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from patchpilot.constants import ReviewDecision
from patchpilot.db.base import Base


class ReviewModel(Base):
    __tablename__ = "reviews"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    patch_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("patch_candidates.id", ondelete="CASCADE"), nullable=False, index=True
    )
    reviewer: Mapped[str] = mapped_column(String(100), nullable=False)
    decision: Mapped[ReviewDecision] = mapped_column(Enum(ReviewDecision), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    decided_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    patch: Mapped[PatchCandidateModel] = relationship(
        "PatchCandidateModel", back_populates="reviews"
    )


from patchpilot.db.models.patch import PatchCandidateModel  # noqa: E402

