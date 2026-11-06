from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field
from patchpilot.constants import PatchState, ReviewDecision
from patchpilot.schemas.pipeline import ValidationReport


class PatchCandidateResponse(BaseModel):
    id: str
    finding_id: str
    attempt: int
    model: str
    prompt_version: str
    unified_diff: str
    explanation: str | None = None
    confidence: float | None = None
    risk_score: float | None = None
    state: PatchState
    version: int
    created_at: datetime


class PatchDetailResponse(PatchCandidateResponse):
    validation_report: ValidationReport | None = None


class ReviewCreate(BaseModel):
    decision: ReviewDecision
    reason: str | None = None
    comment: str | None = None


class ReviewResponse(BaseModel):
    id: str
    patch_id: str
    reviewer: str
    decision: ReviewDecision
    reason: str | None = None
    decided_at: datetime


class BranchRequest(BaseModel):
    branch_name: str | None = None
    commit_message: str | None = None


class BranchResponse(BaseModel):
    branch_name: str
    commit_sha: str
    patch_id: str
    created_at: datetime

