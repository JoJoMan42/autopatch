from __future__ import annotations

import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from patchpilot.db.base import Base


class ProjectModel(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    repo_url: Mapped[str] = mapped_column(Text, nullable=False)
    default_branch: Mapped[str] = mapped_column(String(50), default="main", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    scans: Mapped[list[ScanModel]] = relationship("ScanModel", back_populates="project")
    code_chunks: Mapped[list[CodeChunkModel]] = relationship(
        "CodeChunkModel", back_populates="project"
    )


# Late imports for type annotations if needed
from patchpilot.db.models.scan import ScanModel  # noqa: E402
from patchpilot.db.models.code_chunk import CodeChunkModel  # noqa: E402

