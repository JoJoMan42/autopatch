import pytest
from patchpilot.constants import Role
from patchpilot.core.security import (
    check_role,
    create_access_token,
    create_ws_ticket,
    decode_access_token,
    hash_password,
    verify_password,
    verify_ws_ticket,
)
from patchpilot.errors import AuthenticationError, PermissionDeniedError


def test_password_hashing():
    pw = "SecretP@ssw0rd!"
    hashed = hash_password(pw)
    assert verify_password(pw, hashed)
    assert not verify_password("WrongPassword", hashed)


def test_jwt_token_roundtrip():
    token = create_access_token(user_id="user-123", username="priya", role=Role.DEVELOPER)
    payload = decode_access_token(token)
    assert payload.sub == "user-123"
    assert payload.username == "priya"
    assert payload.role == Role.DEVELOPER


def test_ws_ticket_verification():
    ticket = create_ws_ticket(user_id="user-123", job_id="job-456")
    user_id = verify_ws_ticket(ticket, job_id="job-456")
    assert user_id == "user-123"

    # Mismatched job id fails
    with pytest.raises(AuthenticationError):
        verify_ws_ticket(ticket, job_id="wrong-job")


def test_role_enforcement():
    # Should pass without error
    check_role([Role.ADMIN, Role.REVIEWER], Role.REVIEWER)

    # Should raise PermissionDeniedError
    with pytest.raises(PermissionDeniedError):
        check_role([Role.ADMIN], Role.DEVELOPER)

