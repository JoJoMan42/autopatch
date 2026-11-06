from __future__ import annotations

from typing import Any
from pydantic import BaseModel
from patchpilot.constants import FindingStatus, Severity
from patchpilot.schemas.pipeline import CodeSlice


class FindingResponse(BaseModel):
    id: str
    scan_id: str
    fingerprint: str
    rule_id: str
    cwe: str | None = None
    severity: Severity
    file_path: str
    start_line: int
    end_line: int
    message: str
    status: FindingStatus
    version: int


class FindingDetailResponse(FindingResponse):
    raw_sarif: dict[str, Any] | None = None
    code_slice: CodeSlice | None = None
    cwe_guidance: str | None = None


class FindingFilter(BaseModel):
    scan_id: str | None = None
    severity: Severity | None = None
    cwe: str | None = None
    status: FindingStatus | None = None
    cursor: str | None = None
    limit: int = 20

