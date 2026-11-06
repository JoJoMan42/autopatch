from __future__ import annotations

from enum import Enum


class Role(str, Enum):
    VIEWER = "viewer"
    DEVELOPER = "developer"
    REVIEWER = "reviewer"
    ADMIN = "admin"


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FindingStatus(str, Enum):
    OPEN = "open"
    REPAIR_IN_PROGRESS = "repair_in_progress"
    PATCH_READY = "patch_ready"
    NEEDS_MANUAL_FIX = "needs_manual_fix"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"
    WONT_FIX = "wont_fix"


class PatchState(str, Enum):
    PROPOSED = "proposed"
    GUARD_PASSED = "guard_passed"
    TESTED = "tested"
    RESCANNED = "rescanned"
    READY_FOR_REVIEW = "ready_for_review"
    APPROVED = "approved"
    BRANCH_CREATED = "branch_created"
    REJECTED = "rejected"
    FAILED = "failed"
    ABSTAINED = "abstained"
    SUPERSEDED = "superseded"


class StageName(str, Enum):
    GUARD = "guard"
    BASELINE = "baseline"
    LINT = "lint"
    TESTS = "tests"
    SECURITY_TEST = "security_test"
    RESCAN = "rescan"


class StageOutcome(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    INCONCLUSIVE = "inconclusive"


class Verdict(str, Enum):
    VALIDATED = "validated"
    VALIDATED_WITH_WARNINGS = "validated_with_warnings"
    NOT_VALIDATED = "not_validated"
    INCONCLUSIVE = "inconclusive"


class JobType(str, Enum):
    SCAN = "scan"
    REPAIR = "repair"
    BRANCH = "branch"
    EXPERIMENT = "experiment"


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ReviewDecision(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    REGENERATE = "regenerate"



# ---------------------------------------------------------------------------
# Small shared constants (no logic; no package imports)
# ---------------------------------------------------------------------------

ROLE_RANK: dict[Role, int] = {
    Role.VIEWER: 0,
    Role.DEVELOPER: 1,
    Role.REVIEWER: 2,
    Role.ADMIN: 3,
}

TERMINAL_JOB_STATUSES: frozenset[JobStatus] = frozenset(
    {JobStatus.SUCCEEDED, JobStatus.FAILED, JobStatus.CANCELLED}
)

TERMINAL_PATCH_STATES: frozenset[PatchState] = frozenset(
    {
        PatchState.BRANCH_CREATED,
        PatchState.REJECTED,
        PatchState.FAILED,
        PatchState.ABSTAINED,
        PatchState.SUPERSEDED,
    }
)

PAGE_SIZE_DEFAULT: int = 50
PAGE_SIZE_MAX: int = 200
SUPPORTED_LANGUAGES: tuple[str, ...] = ('python',)
