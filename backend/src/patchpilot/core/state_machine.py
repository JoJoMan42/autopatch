from __future__ import annotations

from typing import Any
from sqlalchemy.orm import Session

from patchpilot.constants import PatchState
from patchpilot.db.models.patch import PatchCandidateModel
from patchpilot.errors import ConflictError, InvalidStateError

# Allowed patch transitions mapping: (from_state, to_state) -> description / validation
ALLOWED_PATCH_TRANSITIONS: set[tuple[PatchState, PatchState]] = {
    (PatchState.PROPOSED, PatchState.GUARD_PASSED),
    (PatchState.PROPOSED, PatchState.ABSTAINED),
    (PatchState.PROPOSED, PatchState.FAILED),
    (PatchState.GUARD_PASSED, PatchState.TESTED),
    (PatchState.GUARD_PASSED, PatchState.FAILED),
    (PatchState.TESTED, PatchState.RESCANNED),
    (PatchState.TESTED, PatchState.FAILED),
    (PatchState.RESCANNED, PatchState.READY_FOR_REVIEW),
    (PatchState.READY_FOR_REVIEW, PatchState.APPROVED),
    (PatchState.READY_FOR_REVIEW, PatchState.REJECTED),
    (PatchState.READY_FOR_REVIEW, PatchState.SUPERSEDED),
    (PatchState.APPROVED, PatchState.BRANCH_CREATED),
}


def transition_patch_state(
    db: Session,
    patch: PatchCandidateModel,
    target_state: PatchState,
    *,
    expected_version: int | None = None,
    actor: str = "system",
    details: dict[str, Any] | None = None,
) -> PatchCandidateModel:
    """Transition patch candidate state with optimistic concurrency check and audit logging."""
    current_state = patch.state

    # 1. Concurrency version check
    if expected_version is not None and patch.version != expected_version:
        raise ConflictError(
            f"Patch {patch.id} version conflict: current={patch.version}, expected={expected_version}"
        )

    # 2. Transition validation
    if (current_state, target_state) not in ALLOWED_PATCH_TRANSITIONS:
        raise InvalidStateError(
            f"Illegal state transition for patch {patch.id}: {current_state.value} -> {target_state.value}"
        )

    # 3. Apply state transition
    patch.state = target_state
    patch.version += 1

    # 4. Record audit event in the same transaction
    from patchpilot.core.audit import record_audit_event

    record_audit_event(
        db,
        actor=actor,
        action="patch.state_transition",
        entity_type="patch",
        entity_id=patch.id,
        payload={
            "from_state": current_state.value,
            "to_state": target_state.value,
            "version": patch.version,
            "details": details or {},
        },
    )

    return patch

