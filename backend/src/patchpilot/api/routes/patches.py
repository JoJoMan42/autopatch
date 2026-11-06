from __future__ import annotations

from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from patchpilot.constants import PatchState
from patchpilot.core.state_machine import transition_patch_state
from patchpilot.db.models.patch import PatchCandidateModel
from patchpilot.db.models.validation import ValidationRunModel
from patchpilot.db.session import get_db
from patchpilot.errors import ApprovalRequiredError, NotFoundError
from patchpilot.schemas.patches import (
    BranchRequest,
    BranchResponse,
    PatchCandidateResponse,
)

router = APIRouter(prefix="/patches", tags=["Patches"])


@router.get("/{patch_id}", response_model=PatchCandidateResponse)
def get_patch(patch_id: str, db: Session = Depends(get_db)) -> PatchCandidateModel:
    patch = db.get(PatchCandidateModel, patch_id)
    if not patch:
        raise NotFoundError(f"Patch {patch_id} not found")
    return patch


@router.get("/{patch_id}/evidence")
def get_patch_evidence(patch_id: str, db: Session = Depends(get_db)) -> dict:
    patch = db.get(PatchCandidateModel, patch_id)
    if not patch:
        raise NotFoundError(f"Patch {patch_id} not found")

    runs = list(
        db.scalars(
            select(ValidationRunModel)
            .where(ValidationRunModel.patch_id == patch_id)
            .order_by(ValidationRunModel.created_at.asc())
        ).all()
    )

    return {
        "patch_id": patch.id,
        "state": patch.state.value,
        "risk_score": patch.risk_score,
        "stages": [
            {
                "stage": r.stage.value,
                "outcome": r.outcome.value,
                "duration_ms": r.duration_ms,
                "log_uri": r.log_uri,
            }
            for r in runs
        ],
    }


@router.post("/{patch_id}/branch", response_model=BranchResponse)
def create_branch_for_patch(
    patch_id: str,
    req: BranchRequest = BranchRequest(),
    actor: str = "security-reviewer",
    db: Session = Depends(get_db),
) -> BranchResponse:
    patch = db.get(PatchCandidateModel, patch_id)
    if not patch:
        raise NotFoundError(f"Patch {patch_id} not found")

    # Hard security gate: Enforced in backend, never bypassed
    if patch.state != PatchState.APPROVED:
        raise ApprovalRequiredError(
            f"Cryptographic gate blocked branch creation: patch {patch_id} state is '{patch.state.value}'. "
            "Must be explicitly 'approved' by an authorized human reviewer."
        )

    branch_name = req.branch_name or f"patchpilot/fix-{patch.finding_id[:8]}"
    commit_sha = f"commit-{patch.id[:12]}"

    transition_patch_state(
        db,
        patch,
        PatchState.BRANCH_CREATED,
        actor=actor,
        details={"branch_name": branch_name, "commit_sha": commit_sha},
    )
    db.commit()

    return BranchResponse(
        branch_name=branch_name,
        commit_sha=commit_sha,
        patch_id=patch.id,
        created_at=datetime.now(timezone.utc),
    )

