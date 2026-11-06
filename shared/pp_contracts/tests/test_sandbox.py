"""Tests for pp_contracts.sandbox – image-ref validation and model strictness."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from pp_contracts.sandbox import (
    ResourceLimits,
    SandboxJobSpec,
    SandboxResult,
    is_pinned_image_ref,
)

# ---------------------------------------------------------------------------
# is_pinned_image_ref
# ---------------------------------------------------------------------------

PINNED_REFS = [
    # name@sha256:<64 hex>
    "myrepo/image@sha256:" + "a" * 64,
    "localhost:5000/runner@sha256:" + "0" * 64,
    "python@sha256:" + "f" * 64,
    # bare sha256:<64 hex>
    "sha256:" + "b" * 64,
]

UNPINNED_REFS = [
    "python:3.11",
    "python:latest",
    "python",
    "myrepo/image:v1.0",
    # wrong digest length
    "sha256:" + "a" * 63,
    "sha256:" + "a" * 65,
    # tag + digest (not supported by our pattern)
    "myrepo/image:v1@sha256:" + "a" * 64,
    "",
    "sha256:",
]


@pytest.mark.parametrize("ref", PINNED_REFS)
def test_is_pinned_image_ref_accepts_valid(ref: str) -> None:
    assert is_pinned_image_ref(ref) is True


@pytest.mark.parametrize("ref", UNPINNED_REFS)
def test_is_pinned_image_ref_rejects_invalid(ref: str) -> None:
    assert is_pinned_image_ref(ref) is False


# ---------------------------------------------------------------------------
# extra='forbid' on all three models
# ---------------------------------------------------------------------------

GOOD_SPEC = dict(
    run_id="run-1",
    stage="scan",
    image="sha256:" + "a" * 64,
    command=["pytest"],
    workspace_id="ws-1",
    labels={"job_id": "job-1"},
)

GOOD_RESULT = dict(
    run_id="run-1",
    status="ok",
    exit_code=0,
    timed_out=False,
    oom_killed=False,
    duration_ms=500,
    stdout_tail="",
    stderr_tail="",
    out_dir="/out",
)


def test_resource_limits_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        ResourceLimits(memory_mb=512, unknown_field=99)  # type: ignore[call-arg]


def test_sandbox_job_spec_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        SandboxJobSpec(**GOOD_SPEC, unknown_field="x")  # type: ignore[call-arg]


def test_sandbox_result_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        SandboxResult(**GOOD_RESULT, unknown_field="x")  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# Valid construction
# ---------------------------------------------------------------------------

def test_sandbox_job_spec_valid() -> None:
    spec = SandboxJobSpec(**GOOD_SPEC)
    assert spec.stage == "scan"
    assert isinstance(spec.limits, ResourceLimits)


def test_sandbox_result_valid() -> None:
    result = SandboxResult(**GOOD_RESULT)
    assert result.status == "ok"
    assert result.exit_code == 0


def test_resource_limits_defaults() -> None:
    lim = ResourceLimits()
    assert lim.memory_mb == 512
    assert lim.timeout_s == 120
