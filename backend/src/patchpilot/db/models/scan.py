from __future__ import annotations

from datetime import datetime

from sqlalchemy import CHAR, CheckConstraint, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from patchpilot.db.base import Base, TimestampMixin, jsonb_type, uuid_fk, uuid_pk


class ScanModel(Base, TimestampMixin):
    """One scanner execution against a project commit."""

    __tablename__ = "scans"
    __table_args__ = (
        CheckConstraint(
            "status IN ('queued', 'running', 'done', 'failed')",
            name="status_values",
        ),
    )

    id: Mapped[str] = uuid_pk()
    project_id: Mapped[str] = uuid_fk("projects.id")
    commit_sha: Mapped[str] = mapped_column(CHAR(40), nullable=False)
    scanner: Mapped[str] = mapped_column(Text, nullable=False)
    scanner_ver: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="queued", server_default="queued"
    )
    # jobs is created in migration 0002; the FK is declared here for the ORM.
    job_id: Mapped[str | None] = uuid_fk("jobs.id", nullable=True, use_alter=True)
    summary: Mapped[dict | None] = mapped_column(jsonb_type(), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    project: Mapped[ProjectModel] = relationship(back_populates="scans", lazy="raise")
    findings: Mapped[list[FindingModel]] = relationship(back_populates="scan", lazy="raise")


from patchpilot.db.models.finding import FindingModel
from patchpilot.db.models.project import ProjectModel
