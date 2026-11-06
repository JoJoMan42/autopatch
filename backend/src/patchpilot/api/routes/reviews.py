from __future__ import annotations

from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from patchpilot.constants import PatchState, ReviewDecision
from patchpilot.core.state_machine import transition_patch_state
from patchpilot.db.models.patch import PatchCandidateModel
from patchpilot.db.models.review import ReviewModel
from patchpilot.db.session import get_db
from patchpilot.errors import InvalidStateError, NotFoundError
from patchpilot.schemas.patches import ReviewCreate, ReviewResponse

router = APIRouter(prefix="/patches", tags=["Reviews"])


@router.post("/{patch_id}/review", response_model=ReviewResponse, status_code=201)
def record_review_decision(
    patch_id: str,
    req: ReviewCreate,
    reviewer: str = "security-reviewer",
    db: Session = Depends(get_db),
) -> ReviewModel:
    patch = db.get(PatchCandidateModel, patch_id)
    if not patch:
        raise NotFoundError(f"Patch {patch_id} not found")

    if patch.state != PatchState.READY_FOR_REVIEW:
        raise InvalidStateError(
            f"Cannot review patch in state '{patch.state.value}'. Must be 'ready_for_review'."
        )

    # Determine target state
    if req.decision == ReviewDecision.APPROVED:
        target_state = PatchState.APPROVED
    elif req.decision == ReviewDecision.REJECTED:
        target_state = PatchState.REJECTED
    else:
        target_state = PatchState.SUPERSEDED

    # Apply state transition
    transition_patch_state(
        db,
        patch,
        target_state,
        actor=reviewer,
        details={"reason": req.reason, "comment": req.comment},
    )

    review = ReviewModel(
        patch_id=patch_id,
        reviewer=reviewer,
        decision=req.decision,
        reason=req.reason or req.comment,
        decided_at=datetime.now(timezone.utc),
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return review

