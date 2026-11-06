from __future__ import annotations

import re
from typing import Callable
from patchpilot.llm.gateway import LLMGateway
from patchpilot.repair.generator import generate_patch
from patchpilot.repair.guard import PatchGuard
from patchpilot.schemas.pipeline import (
    ContextBundle,
    GuardReport,
    NormalizedFinding,
    PatchProposal,
    ValidationReport,
    Verdict,
)


def sanitize_feedback(text: str, max_length: int = 1000) -> str:
    """Sanitize and truncate feedback text to prevent prompt injection from logs."""
    # Strip non-printable ASCII control characters except \n and \t
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    # Neutralize instruction-like markers
    cleaned = cleaned.replace("[SYSTEM]", "").replace("[TASK]", "").replace("[DATA", "")
    return cleaned[:max_length].strip()


class RepairLoop:
    """Executes iterative repair loop with static guard and dynamic validation feedback."""

    def __init__(
        self,
        gateway: LLMGateway,
        guard: PatchGuard | None = None,
        max_attempts: int = 3,
    ) -> None:
        self.gateway = gateway
        self.guard = guard or PatchGuard()
        self.max_attempts = max_attempts

    def execute(
        self,
        finding: NormalizedFinding,
        context: ContextBundle,
        validator_fn: Callable[[PatchProposal, int], ValidationReport] | None = None,
        allowed_imports: set[str] | None = None,
        model: str | None = None,
    ) -> tuple[PatchProposal, GuardReport, ValidationReport | None, int]:
        feedback: str | None = None
        last_proposal: PatchProposal | None = None
        last_guard: GuardReport | None = None
        last_validation: ValidationReport | None = None

        for attempt in range(1, self.max_attempts + 1):
            proposal = generate_patch(
                finding=finding,
                context=context,
                gateway=self.gateway,
                feedback=feedback,
                allowed_imports=allowed_imports,
                model=model,
            )
            last_proposal = proposal

            if proposal.status == "cannot_fix":
                return proposal, GuardReport(ok=False, issues=[], changed_files=[], changed_lines=0), None, attempt

            # Apply static guard check
            guard_report = self.guard.verify_patch(
                diff_text=proposal.diff,
                expected_target_file=finding.file_path,
                cwe=finding.cwe,
                allowed_imports=allowed_imports,
            )
            last_guard = guard_report

            if not guard_report.ok:
                err_summary = "; ".join(i.message for i in guard_report.issues)
                feedback = sanitize_feedback(f"Static guard check failed: {err_summary}")
                continue

            # Run dynamic validation if validator callback provided
            if validator_fn:
                val_report = validator_fn(proposal, attempt)
                last_validation = val_report

                if val_report.verdict in (Verdict.VALIDATED, Verdict.VALIDATED_WITH_WARNINGS):
                    return proposal, guard_report, val_report, attempt

                failures = val_report.new_failures or [f.message for f in val_report.new_findings]
                feedback = sanitize_feedback(f"Validation failed: {'; '.join(failures[:3])}")
            else:
                return proposal, guard_report, None, attempt

        return (
            last_proposal or PatchProposal(status="cannot_fix", reason="All attempts failed"),
            last_guard or GuardReport(ok=False, issues=[], changed_files=[], changed_lines=0),
            last_validation,
            self.max_attempts,
        )

