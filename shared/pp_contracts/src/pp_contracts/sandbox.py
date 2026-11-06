from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field


class ResourceLimits(BaseModel):
    memory_mb: int = 512
    cpus: float = 1.0
    pids: int = 128
    timeout_s: int = 120
    tmpfs_mb: int = 64
    output_bytes: int = 1_000_000


class SandboxJobSpec(BaseModel):
    run_id: str
    stage: Literal["prepare", "scan", "validate"]
    image: str  # must be pinned by digest
    command: list[str]
    workspace_id: str  # /workspaces/<id>/src is read-only, /out is writable
    network: Literal["none", "mirror"] = "none"
    limits: ResourceLimits = Field(default_factory=ResourceLimits)
    env: dict[str, str] = Field(default_factory=dict)
    labels: dict[str, str] = Field(default_factory=dict)  # must include job_id


class SandboxResult(BaseModel):
    run_id: str
    status: Literal["ok", "failed", "timeout", "oom", "error"]
    exit_code: int | None
    timed_out: bool
    oom_killed: bool
    duration_ms: int
    stdout_tail: str
    stderr_tail: str
    out_dir: str

