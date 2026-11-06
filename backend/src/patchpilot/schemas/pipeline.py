from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field

from patchpilot.constants import Severity, StageName, StageOutcome, Verdict


class NormalizedFinding(BaseModel):
    scanner: str
    rule_id: str
    cwe: str | None = None  # normalized form such as CWE-89
    severity: Severity
    file_path: str  # repo-relative, forward slashes
    start_line: int
    end_line: int
    message: str
    fingerprint: str
    raw: dict[str, Any] = Field(default_factory=dict)


class CodeSlice(BaseModel):
    file_path: str
    function_name: str | None = None
    start_line: int
    end_line: int
    source: str  # full enclosing function or class text
    slice_lines: list[int]
    slice_source: str
    external_params: list[str] = Field(default_factory=list)


class ContextSnippet(BaseModel):
    kind: Literal["callers", "callees", "helper", "similar", "cwe_guidance", "example"]
    file_path: str | None = None
    start_line: int | None = None
    end_line: int | None = None
    text: str
    score: float | None = None
    chunk_id: str | None = None


class ContextBundle(BaseModel):
    finding_id: str
    cwe: str | None
    code_slice: CodeSlice
    snippets: list[ContextSnippet]
    token_estimate: int
    retrieved_chunk_ids: list[str] = Field(default_factory=list)


class PatchProposal(BaseModel):
    status: Literal["fixed", "cannot_fix"]
    analysis: str = ""
    diff: str = ""
    explanation: str = ""
    assumptions: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    reason: str | None = None


class GuardIssue(BaseModel):
    code: str  # for example IMPORT_NOT_ALLOWED
    message: str
    severity: Literal["error", "warning"] = "error"
    file_path: str | None = None
    line: int | None = None


class GuardReport(BaseModel):
    ok: bool
    issues: list[GuardIssue]
    changed_files: list[str]
    changed_lines: int


class StageResult(BaseModel):
    stage: StageName
    outcome: StageOutcome
    duration_ms: int
    summary: str
    log_uri: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class ValidationReport(BaseModel):
    patch_id: str
    verdict: Verdict
    stages: list[StageResult]
    baseline_failures: list[str] = Field(default_factory=list)
    new_failures: list[str] = Field(default_factory=list)
    new_findings: list[NormalizedFinding] = Field(default_factory=list)
    flaky_tests: list[str] = Field(default_factory=list)


class RepairOptions(BaseModel):
    max_attempts: int = 3
    candidates: int = 1
    model: str | None = None
    run_security_test: bool = True
    use_judge: bool = False
    variant: str = "V4"  # evaluation variant V0 to V5

