from __future__ import annotations

from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field
from patchpilot.constants import JobStatus, JobType


class JobResponse(BaseModel):
    id: str
    type: JobType
    status: JobStatus
    entity_id: str | None = None
    stage: str | None = None
    progress_pct: int = 0
    error: str | None = None
    created_at: datetime
    updated_at: datetime


class JobEventPayload(BaseModel):
    v: int = 1
    seq: int
    type: str
    job_id: str
    ts: datetime
    data: dict[str, Any] = Field(default_factory=dict)

