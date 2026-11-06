import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from patchpilot.constants import PatchState
from patchpilot.db.base import Base
from patchpilot.db.models.patch import PatchCandidateModel
from patchpilot.db.session import get_db
from patchpilot.main import app


@pytest.fixture
def client_and_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    session = TestingSessionLocal()
    yield client, session
    app.dependency_overrides.clear()
    session.close()


def test_server_enforces_approval_gate_before_branch(client_and_session):
    client, session = client_and_session

    patch = PatchCandidateModel(
        finding_id="test-finding-1",
        attempt=1,
        model="test-model",
        prompt_version="v1",
        unified_diff="--- a/shop/db.py\n+++ b/shop/db.py\n",
        state=PatchState.READY_FOR_REVIEW,
        version=1,
    )
    session.add(patch)
    session.commit()
    session.refresh(patch)

    # 1. Direct attempt to create branch before human review MUST FAIL with 409
    res = client.post(f"/api/v1/patches/{patch.id}/branch")
    assert res.status_code == 409
    assert "Cryptographic gate blocked branch creation" in res.json()["detail"]

    # 2. Human reviewer approves patch
    review_res = client.post(
        f"/api/v1/patches/{patch.id}/review",
        json={"decision": "approved", "comment": "Verified secure parameterized fix"},
    )
    assert review_res.status_code == 201

    # 3. Branch creation now succeeds
    branch_res = client.post(f"/api/v1/patches/{patch.id}/branch")
    assert branch_res.status_code == 200
    assert branch_res.json()["patch_id"] == patch.id
    assert "patchpilot/fix-" in branch_res.json()["branch_name"]

