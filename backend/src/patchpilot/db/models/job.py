from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Integer, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from patchpilot.constants import JobStatus, JobType
from patchpilot.db.base import (
    Base,
    EnumText,
    TimestampMixin,
    bigserial_pk,
    enum_check,
    jsonb_type,
    utcnow,
    uuid_fk,
    uuid_pk,
)


class JobModel(Base, TimestampMixin):
    """Background scan, repair, branch, or experiment job."""

    __tablename__ = "jobs"
    __table_args__ = (
        enum_check("type", JobType),
        enum_check("status", JobStatus),
    )

    id: Mapped[str] = uuid_pk()
    type: Mapped[JobType] = mapped_column(EnumText(JobType), nullable=False)
    status: Mapped[JobStatus] = mapped_column(
        EnumText(JobStatus),
        nullable=False,
        default=JobStatus.QUEUED,
        server_default="queued",
    )
    project_id: Mapped[str | None] = uuid_fk("projects.id", nullable=True)
    finding_id: Mapped[str | None] = uuid_fk("findings.id", nullable=True)
    patch_id: Mapped[str | None] = uuid_fk("patch_candidates.id", nullable=True)
    # experiments is created in migration 0003; the FK is declared here for the ORM.
    experiment_id: Mapped[str | None] = uuid_fk(
        "experiments.id", nullable=True, use_alter=True
    )
    payload: Mapped[dict[str, Any]] = mapped_column(jsonb_type(), nullable=False, default=dict)
    result: Mapped[dict[str, Any] | None] = mapped_column(jsonb_type(), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str | None] = uuid_fk("users.id", nullable=True)
    correlation_id: Mapped[str] = mapped_column(Text, nullable=False)
    celery_task_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    events: Mapped[list[JobEventModel]] = relationship(
        back_populates="job",
        lazy="raise",
        order_by="JobEventModel.seq",
    )


class JobEventModel(Base):
    """Ordered job event. The table is append-only in PostgreSQL."""

    __tablename__ = "job_events"
    __table_args__ = (UniqueConstraint("job_id", "seq", name="uq_job_events_job_id_seq"),)

    id: Mapped[int] = bigserial_pk()
    job_id: Mapped[str] = uuid_fk("jobs.id")
    seq: Mapped[int] = mapped_column(Integer, nullable=False)
    type: Mapped[str] = mapped_column(Text, nullable=False)
    data: Mapped[dict[str, Any]] = mapped_column(jsonb_type(), nullable=False, default=dict)
    ts: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        server_default="now()",
    )

    job: Mapped[JobModel] = relationship(back_populates="events", lazy="raise")
