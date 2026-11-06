from __future__ import annotations

import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from patchpilot.constants import JobStatus, JobType
from patchpilot.db.models.finding import FindingModel
from patchpilot.db.models.job import JobModel
from patchpilot.db.session import get_db
from patchpilot.errors import NotFoundError
from patchpilot.schemas.pipeline import RepairOptions

router = APIRouter(prefix="/findings", tags=["Repair"])


@router.post("/{finding_id}/repair", status_code=202)
def start_repair(
    finding_id: str,
    options: RepairOptions = RepairOptions(),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    finding = db.get(FindingModel, finding_id)
    if not finding:
        raise NotFoundError(f"Finding {finding_id} not found")

    job = JobModel(
        type=JobType.REPAIR,
        status=JobStatus.QUEUED,
        entity_id=finding_id,
        stage="queued",
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    return {
        "job_id": job.id,
        "status": "queued",
        "events": f"/ws/v1/jobs/{job.id}",
    }

