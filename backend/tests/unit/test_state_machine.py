import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from patchpilot.constants import PatchState
from patchpilot.core.state_machine import transition_patch_state
from patchpilot.db.base import Base
from patchpilot.db.models.finding import FindingModel
from patchpilot.db.models.patch import PatchCandidateModel
from patchpilot.db.models.project import ProjectModel
from patchpilot.db.models.scan import ScanModel
from patchpilot.errors import ConflictError, InvalidStateError


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_allowed_patch_transition(db_session: Session):
    patch = PatchCandidateModel(
        finding_id="test-finding",
        attempt=1,
        model="test-model",
        prompt_version="v1",
        unified_diff="--- a\n+++ b",
        state=PatchState.PROPOSED,
        version=1,
    )
    db_session.add(patch)
    db_session.flush()

    # PROPOSED -> GUARD_PASSED is allowed
    transition_patch_state(db_session, patch, PatchState.GUARD_PASSED)
    assert patch.state == PatchState.GUARD_PASSED
    assert patch.version == 2

    # GUARD_PASSED -> TESTED is allowed
    transition_patch_state(db_session, patch, PatchState.TESTED)
    assert patch.state == PatchState.TESTED
    assert patch.version == 3


def test_forbidden_patch_transition_raises_error(db_session: Session):
    patch = PatchCandidateModel(
        finding_id="test-finding",
        attempt=1,
        model="test-model",
        prompt_version="v1",
        unified_diff="--- a\n+++ b",
        state=PatchState.PROPOSED,
        version=1,
    )
    db_session.add(patch)
    db_session.flush()

    # PROPOSED -> APPROVED is illegal (skips guard and tests)
    with pytest.raises(InvalidStateError):
        transition_patch_state(db_session, patch, PatchState.APPROVED)


def test_optimistic_concurrency_conflict(db_session: Session):
    patch = PatchCandidateModel(
        finding_id="test-finding",
        attempt=1,
        model="test-model",
        prompt_version="v1",
        unified_diff="--- a\n+++ b",
        state=PatchState.PROPOSED,
        version=2,
    )
    db_session.add(patch)
    db_session.flush()

    # Pass expected_version=1 when current version is 2
    with pytest.raises(ConflictError):
        transition_patch_state(
            db_session,
            patch,
            PatchState.GUARD_PASSED,
            expected_version=1,
        )

