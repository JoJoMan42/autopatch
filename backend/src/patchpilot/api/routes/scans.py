from __future__ import annotations

import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from patchpilot.db.models.project import ProjectModel
from patchpilot.db.models.scan import ScanModel
from patchpilot.db.session import get_db
from patchpilot.errors import NotFoundError
from patchpilot.schemas.projects import ScanCreate, ScanResponse

router = APIRouter(tags=["Scans"])


@router.post("/projects/{project_id}/scans", response_model=ScanResponse, status_code=202)
def start_scan(
    project_id: str,
    req: ScanCreate,
    db: Session = Depends(get_db),
) -> ScanModel:
    project = db.get(ProjectModel, project_id)
    if not project:
        raise NotFoundError(f"Project {project_id} not found")

    scan = ScanModel(
        project_id=project_id,
        commit_sha=req.commit_sha,
        scanner=",".join(req.scanners),
        scanner_ver="1.0.0",
        status="queued",
        started_at=datetime.now(timezone.utc),
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)
    return scan


@router.get("/scans/{scan_id}", response_model=ScanResponse)
def get_scan(scan_id: str, db: Session = Depends(get_db)) -> ScanModel:
    scan = db.get(ScanModel, scan_id)
    if not scan:
        raise NotFoundError(f"Scan {scan_id} not found")
    return scan

