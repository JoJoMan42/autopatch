from __future__ import annotations

from patchpilot.constants import Verdict
from patchpilot.schemas.pipeline import NormalizedFinding, ValidationReport


def determine_verdict(
    patch_id: str,
    baseline_failures: list[str],
    patched_failures: list[str],
    target_finding: NormalizedFinding,
    rescan_findings: list[NormalizedFinding],
    has_timeout: bool = False,
    has_crash: bool = False,
    security_test_passed: bool = True,
) -> tuple[Verdict, list[str], list[NormalizedFinding]]:
    """Apply the verdict rules from Section 4.4 of the PatchPilot System Design."""
    if has_timeout or has_crash:
        return Verdict.INCONCLUSIVE, [], []

    new_failures = sorted(list(set(patched_failures) - set(baseline_failures)))
    if new_failures:
        return Verdict.NOT_VALIDATED, new_failures, []

    if not security_test_passed:
        return Verdict.NOT_VALIDATED, ["Security regression test failed"], []

    # Check if target finding fingerprint is gone
    target_still_present = any(
        f.fingerprint == target_finding.fingerprint for f in rescan_findings
    )
    if target_still_present:
        return Verdict.NOT_VALIDATED, [], []

    # Check for newly introduced findings
    new_findings = [
        f for f in rescan_findings if f.fingerprint != target_finding.fingerprint
    ]
    if any(f.severity.value in ("critical", "high") for f in new_findings):
        return Verdict.NOT_VALIDATED, [], new_findings

    if baseline_failures or new_findings:
        return Verdict.VALIDATED_WITH_WARNINGS, [], new_findings

    return Verdict.VALIDATED, [], []

