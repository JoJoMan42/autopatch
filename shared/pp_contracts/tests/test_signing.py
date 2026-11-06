"""Tests for pp_contracts.signing – HMAC round-trip, wrong secret, stale timestamp."""

from __future__ import annotations

import time

import pytest

from pp_contracts.signing import sign_request, verify_request

SECRET = "test-secret-32-bytes-long-enough"
BODY = b'{"run_id":"run-1","stage":"scan"}'


# ---------------------------------------------------------------------------
# Happy-path round-trip
# ---------------------------------------------------------------------------

def test_round_trip_accepts_valid_signature() -> None:
    ts = int(time.time())
    sig = sign_request(BODY, SECRET, ts)
    assert verify_request(BODY, sig, SECRET, ts, now=ts) is True


def test_round_trip_with_explicit_now() -> None:
    ts = 1_700_000_000
    sig = sign_request(BODY, SECRET, ts)
    assert verify_request(BODY, sig, SECRET, ts, now=ts) is True


# ---------------------------------------------------------------------------
# Wrong secret
# ---------------------------------------------------------------------------

def test_wrong_secret_rejected() -> None:
    ts = int(time.time())
    sig = sign_request(BODY, SECRET, ts)
    assert verify_request(BODY, sig, "wrong-secret", ts, now=ts) is False


def test_tampered_body_rejected() -> None:
    ts = int(time.time())
    sig = sign_request(BODY, SECRET, ts)
    assert verify_request(b"tampered", sig, SECRET, ts, now=ts) is False


# ---------------------------------------------------------------------------
# Stale timestamp
# ---------------------------------------------------------------------------

def test_timestamp_too_old_rejected() -> None:
    ts = int(time.time()) - 120  # 120 s ago; default max_skew_s = 60
    sig = sign_request(BODY, SECRET, ts)
    assert verify_request(BODY, sig, SECRET, ts) is False


def test_timestamp_in_the_future_rejected() -> None:
    ts = int(time.time()) + 120
    sig = sign_request(BODY, SECRET, ts)
    assert verify_request(BODY, sig, SECRET, ts) is False


def test_timestamp_just_within_skew_accepted() -> None:
    now = int(time.time())
    ts = now - 59  # just inside the 60-second window
    sig = sign_request(BODY, SECRET, ts)
    assert verify_request(BODY, sig, SECRET, ts, now=now) is True


def test_custom_max_skew() -> None:
    now = int(time.time())
    ts = now - 300  # 5 minutes old
    sig = sign_request(BODY, SECRET, ts)
    # Rejected with default skew
    assert verify_request(BODY, sig, SECRET, ts, now=now) is False
    # Accepted with generous skew
    assert verify_request(BODY, sig, SECRET, ts, now=now, max_skew_s=600) is True


# ---------------------------------------------------------------------------
# Malformed / edge-case inputs – must return False, never raise
# ---------------------------------------------------------------------------

def test_empty_signature_returns_false() -> None:
    ts = int(time.time())
    assert verify_request(BODY, "", SECRET, ts, now=ts) is False


def test_non_hex_signature_returns_false() -> None:
    ts = int(time.time())
    assert verify_request(BODY, "not-a-hex-sig!!", SECRET, ts, now=ts) is False


def test_empty_body_accepted_when_valid() -> None:
    ts = int(time.time())
    sig = sign_request(b"", SECRET, ts)
    assert verify_request(b"", sig, SECRET, ts, now=ts) is True


# ---------------------------------------------------------------------------
# sign_request is deterministic
# ---------------------------------------------------------------------------

def test_sign_request_deterministic() -> None:
    ts = 1_700_000_000
    assert sign_request(BODY, SECRET, ts) == sign_request(BODY, SECRET, ts)


def test_sign_request_different_timestamps_differ() -> None:
    assert sign_request(BODY, SECRET, 1_000) != sign_request(BODY, SECRET, 2_000)
