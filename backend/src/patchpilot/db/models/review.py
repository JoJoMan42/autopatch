from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from patchpilot.constants import ReviewDecision
from patchpilot.db.base import Base, EnumText, enum_check, utcnow, uuid_fk, uuid_pk


class ReviewModel(Base):
    """Human review of a patch. decided_at replaces created_at."""

    __tablename__ = "reviews"
    __table_args__ = (enum_check("decision", ReviewDecision),)

    id: Mapped[str] = uuid_pk()
    patch_id: Mapped[str] = uuid_fk("patch_candidates.id")
    reviewer_id: Mapped[str] = uuid_fk("users.id")
    decision: Mapped[ReviewDecision] = mapped_column(EnumText(ReviewDecision), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    include_generated_test: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    decided_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        server_default="now()",
    )

    patch: Mapped[PatchCandidateModel] = relationship(back_populates="reviews", lazy="raise")


from patchpilot.db.models.patch import PatchCandidateModel
