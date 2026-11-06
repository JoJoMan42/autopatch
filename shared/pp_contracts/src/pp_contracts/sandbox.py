from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# Accepts: name@sha256:<64 hex>  or  sha256:<64 hex>
#
# The ``name`` component follows Docker image-reference conventions:
#   - optional registry host with optional port: ``host(:port)?/``
#   - one or more path segments separated by ``/``
#   - NO tag (e.g. ``:latest`` or ``:v1`` before the ``@``) — tags return False.
#
# Examples that return True:
#   sha256:<64hex>
#   python@sha256:<64hex>
#   localhost:5000/runner@sha256:<64hex>
#   myrepo/image@sha256:<64hex>
#
# Examples that return False:
#   python:3.11                         (tag, no digest)
#   myrepo/image:v1@sha256:<64hex>      (tag + digest)
#   sha256:<63hex>                      (wrong digest length)
_NAME_PART = r"[a-zA-Z0-9_.\-]+(:\d+)?(/[a-zA-Z0-9_.\-]+)*"
IMAGE_REF_PATTERN: re.Pattern[str] = re.compile(
    rf"^(?:{_NAME_PART}@)?sha256:[0-9a-f]{{64}}$"
)


def is_pinned_image_ref(ref: str) -> bool:
    """Return True only for name@sha256:<64 hex> or bare sha256:<64 hex> refs.

    Tags such as 'latest' or plain repository names return False.
    """
    return bool(IMAGE_REF_PATTERN.match(ref))


class ResourceLimits(BaseModel):
    """Resource caps applied to every sandbox container."""

    model_config = ConfigDict(extra="forbid")

    memory_mb: int = 512
    cpus: float = 1.0
    pids: int = 128
    timeout_s: int = 120
    tmpfs_mb: int = 64
    output_bytes: int = 1_000_000


class SandboxJobSpec(BaseModel):
    """Specification for a sandbox job submitted to the runner."""

    model_config = ConfigDict(extra="forbid")

    run_id: str
    stage: Literal["prepare", "scan", "validate"]
    image: str  # must be pinned by digest; validated by is_pinned_image_ref
    command: list[str]
    workspace_id: str  # /workspaces/<id>/src is read-only, /out is writable
    network: Literal["none", "mirror"] = "none"
    limits: ResourceLimits = Field(default_factory=ResourceLimits)
    env: dict[str, str] = Field(default_factory=dict)
    labels: dict[str, str] = Field(default_factory=dict)  # must include job_id


class SandboxResult(BaseModel):
    """Result returned by the runner after a sandbox job completes."""

    model_config = ConfigDict(extra="forbid")

    run_id: str
    status: Literal["ok", "failed", "timeout", "oom", "error"]
    exit_code: int | None
    timed_out: bool
    oom_killed: bool
    duration_ms: int
    stdout_tail: str
    stderr_tail: str
    out_dir: str
