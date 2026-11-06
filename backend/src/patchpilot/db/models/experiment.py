from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    CHAR,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from patchpilot.db.base import Base, TimestampMixin, jsonb_type, uuid_fk, uuid_pk


class BenchmarkCaseModel(Base, TimestampMixin):
    """Ground-truth evaluation case. id is the case identifier, not a UUID."""

    __tablename__ = "benchmark_cases"
    __table_args__ = (
        CheckConstraint("source IN ('injected', 'curated')", name="source_values"),
        CheckConstraint("split IN ('dev', 'test')", name="split_values"),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    source: Mapped[str] = mapped_column(Text, nullable=False)
    cwe: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str] = mapped_column(String(32), nullable=False)
    project_ref: Mapped[str] = mapped_column(Text, nullable=False)
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    line: Mapped[int] = mapped_column(Integer, nullable=False)
    split: Mapped[str] = mapped_column(Text, nullable=False)
    ground_truth: Mapped[dict[str, Any]] = mapped_column(jsonb_type(), nullable=False)

    runs: Mapped[list[ExperimentRunModel]] = relationship(back_populates="case", lazy="raise")


class ExperimentModel(Base, TimestampMixin):
    """One benchmark experiment configuration."""

    __tablename__ = "experiments"

    id: Mapped[str] = uuid_pk()
    name: Mapped[str] = mapped_column(Text, nullable=False)
    config: Mapped[dict[str, Any]] = mapped_column(jsonb_type(), nullable=False)
    git_sha: Mapped[str] = mapped_column(CHAR(40), nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    job_id: Mapped[str | None] = uuid_fk("jobs.id", nullable=True)
    created_by: Mapped[str] = uuid_fk("users.id")
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    runs: Mapped[list[ExperimentRunModel]] = relationship(
        back_populates="experiment",
        lazy="raise",
    )


class ExperimentRunModel(Base, TimestampMixin):
    """One sample of one case under one experiment variant."""

    __tablename__ = "experiment_runs"
    __table_args__ = (
        UniqueConstraint(
            "experiment_id",
            "case_id",
            "variant",
            "sample_idx",
            name="uq_experiment_runs_case_variant_sample",
        ),
    )

    id: Mapped[str] = uuid_pk()
    experiment_id: Mapped[str] = uuid_fk("experiments.id")
    case_id: Mapped[str] = mapped_column(
        Text,
        ForeignKey("benchmark_cases.id", ondelete="RESTRICT"),
        nullable=False,
    )
    variant: Mapped[str] = mapped_column(Text, nullable=False)
    sample_idx: Mapped[int] = mapped_column(Integer, nullable=False)
    patch_id: Mapped[str | None] = uuid_fk("patch_candidates.id", nullable=True)
    finding_id: Mapped[str | None] = uuid_fk("findings.id", nullable=True)
    outcome: Mapped[dict[str, Any]] = mapped_column(jsonb_type(), nullable=False)

    experiment: Mapped[ExperimentModel] = relationship(back_populates="runs", lazy="raise")
    case: Mapped[BenchmarkCaseModel] = relationship(back_populates="runs", lazy="raise")
