from __future__ import annotations

import uuid
from typing import Any
from sqlalchemy import (
    Enum,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from patchpilot.constants import FindingStatus, Severity
from patchpilot.db.base import Base


class FindingModel(Base):
    __tablename__ = "findings"
    __table_args__ = (
        UniqueConstraint("scan_id", "fingerprint", name="uq_scan_fingerprint"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    scan_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("scans.id", ondelete="CASCADE"), nullable=False, index=True
    )
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    rule_id: Mapped[str] = mapped_column(String(100), nullable=False)
    cwe: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    severity: Mapped[Severity] = mapped_column(Enum(Severity), nullable=False, index=True)
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    start_line: Mapped[int] = mapped_column(Integer, nullable=False)
    end_line: Mapped[int] = mapped_column(Integer, nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    raw_sarif: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    status: Mapped[FindingStatus] = mapped_column(
        Enum(FindingStatus), default=FindingStatus.OPEN, nullable=False, index=True
    )
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    scan: Mapped[ScanModel] = relationship("ScanModel", back_populates="findings")
    patches: Mapped[list[PatchCandidateModel]] = relationship(
        "PatchCandidateModel", back_populates="finding"
    )


from patchpilot.db.models.scan import ScanModel  # noqa: E402
from patchpilot.db.models.patch import PatchCandidateModel  # noqa: E402

