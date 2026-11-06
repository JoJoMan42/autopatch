from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from patchpilot.constants import FindingStatus, Severity
from patchpilot.context.knowledge_base import get_cwe_guidance
from patchpilot.db.models.finding import FindingModel
from patchpilot.db.session import get_db
from patchpilot.errors import NotFoundError
from patchpilot.schemas.findings import FindingDetailResponse, FindingResponse

router = APIRouter(prefix="/findings", tags=["Findings"])


@router.get("", response_model=list[FindingResponse])
def list_findings(
    scan_id: str | None = None,
    severity: Severity | None = None,
    status: FindingStatus | None = None,
    cwe: str | None = None,
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[FindingModel]:
    stmt = select(FindingModel)
    if scan_id:
        stmt = stmt.where(FindingModel.scan_id == scan_id)
    if severity:
        stmt = stmt.where(FindingModel.severity == severity)
    if status:
        stmt = stmt.where(FindingModel.status == status)
    if cwe:
        stmt = stmt.where(FindingModel.cwe == cwe)

    stmt = stmt.order_by(FindingModel.start_line.asc()).limit(limit)
    return list(db.scalars(stmt).all())


@router.get("/{finding_id}", response_model=FindingDetailResponse)
def get_finding_detail(finding_id: str, db: Session = Depends(get_db)) -> dict:
    finding = db.get(FindingModel, finding_id)
    if not finding:
        raise NotFoundError(f"Finding {finding_id} not found")

    guidance = get_cwe_guidance(finding.cwe)

    return {
        "id": finding.id,
        "scan_id": finding.scan_id,
        "fingerprint": finding.fingerprint,
        "rule_id": finding.rule_id,
        "cwe": finding.cwe,
        "severity": finding.severity,
        "file_path": finding.file_path,
        "start_line": finding.start_line,
        "end_line": finding.end_line,
        "message": finding.message,
        "status": finding.status,
        "version": finding.version,
        "raw_sarif": finding.raw_sarif,
        "cwe_guidance": guidance,
    }

