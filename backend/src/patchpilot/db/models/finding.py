from __future__ import annotations

from typing import Any

from sqlalchemy import Index, Integer, Text, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from patchpilot.constants import FindingStatus, Severity
from patchpilot.db.base import (
    Base,
    EnumText,
    TimestampMixin,
    enum_check,
    jsonb_type,
    uuid_fk,
    uuid_pk,
)


class FindingModel(Base, TimestampMixin):
    """A normalized scanner finding. version is updated only by the state machine."""

    __tablename__ = "findings"
    __table_args__ = (
        UniqueConstraint("scan_id", "fingerprint", name="uq_findings_scan_id_fingerprint"),
        enum_check("severity", Severity),
        enum_check("status", FindingStatus),
        Index("ix_findings_scan_id_severity", "scan_id", "severity"),
        Index(
            "ix_findings_status_open",
            "status",
            postgresql_where=text("status = 'open'"),
        ),
    )

    id: Mapped[str] = uuid_pk()
    scan_id: Mapped[str] = uuid_fk("scans.id")
    project_id: Mapped[str] = uuid_fk("projects.id")
    fingerprint: Mapped[str] = mapped_column(Text, nullable=False)
    rule_id: Mapped[str] = mapped_column(Text, nullable=False)
    scanner: Mapped[str] = mapped_column(Text, nullable=False)
    cwe: Mapped[str | None] = mapped_column(Text, nullable=True)
    severity: Mapped[Severity] = mapped_column(EnumText(Severity), nullable=False)
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    start_line: Mapped[int] = mapped_column(Integer, nullable=False)
    end_line: Mapped[int] = mapped_column(Integer, nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    raw_sarif: Mapped[dict[str, Any]] = mapped_column(jsonb_type(), nullable=False)
    code_slice: Mapped[dict[str, Any] | None] = mapped_column(jsonb_type(), nullable=True)
    status: Mapped[FindingStatus] = mapped_column(
        EnumText(FindingStatus),
        nullable=False,
        default=FindingStatus.OPEN,
        server_default="open",
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")

    scan: Mapped[ScanModel] = relationship(back_populates="findings", lazy="raise")
    patches: Mapped[list[PatchCandidateModel]] = relationship(
        back_populates="finding",
        lazy="raise",
    )


from patchpilot.db.models.patch import PatchCandidateModel
from patchpilot.db.models.scan import ScanModel
