from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    repo_url: str
    default_branch: str = "main"


class ProjectResponse(BaseModel):
    id: str
    name: str
    repo_url: str
    default_branch: str
    created_at: datetime


class ScanCreate(BaseModel):
    commit_sha: str = Field(..., min_length=7, max_length=40)
    scanners: list[str] = Field(default_factory=lambda: ["semgrep", "bandit"])


class ScanResponse(BaseModel):
    id: str
    project_id: str
    commit_sha: str
    scanner: str
    scanner_ver: str
    status: str
    started_at: datetime | None = None
    finished_at: datetime | None = None

