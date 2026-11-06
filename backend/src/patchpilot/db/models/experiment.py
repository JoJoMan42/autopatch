from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any
from sqlalchemy import DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from patchpilot.db.base import Base


class BenchmarkCaseModel(Base):
    __tablename__ = "benchmark_cases"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    language: Mapped[str] = mapped_column(String(30), default="python", nullable=False)
    cwe: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    repo_ref: Mapped[str] = mapped_column(Text, nullable=False)
    ground_truth: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    runs: Mapped[list[ExperimentRunModel]] = relationship(
        "ExperimentRunModel", back_populates="case"
    )


class ExperimentModel(Base):
    __tablename__ = "experiments"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    config: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    git_sha: Mapped[str] = mapped_column(String(40), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="running", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    runs: Mapped[list[ExperimentRunModel]] = relationship(
        "ExperimentRunModel", back_populates="experiment"
    )


class ExperimentRunModel(Base):
    __tablename__ = "experiment_runs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    experiment_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    case_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("benchmark_cases.id", ondelete="CASCADE"), nullable=False, index=True
    )
    patch_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    variant: Mapped[str] = mapped_column(String(20), nullable=False)
    outcome: Mapped[str] = mapped_column(String(30), nullable=False)
    metrics: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    experiment: Mapped[ExperimentModel] = relationship("ExperimentModel", back_populates="runs")
    case: Mapped[BenchmarkCaseModel] = relationship("BenchmarkCaseModel", back_populates="runs")

