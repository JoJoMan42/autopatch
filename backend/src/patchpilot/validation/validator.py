from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

from patchpilot.constants import StageName, StageOutcome, Verdict
from patchpilot.scanning.adapters.bandit import BanditAdapter
from patchpilot.schemas.pipeline import (
    NormalizedFinding,
    PatchProposal,
    StageResult,
    ValidationReport,
)
from patchpilot.validation.verdict import determine_verdict
from patchpilot.validation.workspace import EphemeralWorkspace


class PatchValidator:
    """Executes staged validation pipeline for candidate patch proposals."""

    def __init__(self, scanner_adapter: BanditAdapter | None = None) -> None:
        self.scanner = scanner_adapter or BanditAdapter()

    def validate_patch(
        self,
        patch_id: str,
        proposal: PatchProposal,
        target_finding: NormalizedFinding,
        repo_dir: Path | str,
    ) -> ValidationReport:
        stages: list[StageResult] = []

        with EphemeralWorkspace(repo_dir) as ws:
            # Stage 1: Baseline tests
            start_t = time.perf_counter()
            baseline_proc = subprocess.run(
                [sys.executable, "-m", "pytest", "-q"],
                cwd=str(ws),
                capture_output=True,
                text=True,
            )
            base_duration = int((time.perf_counter() - start_t) * 1000)
            baseline_failures: list[str] = []
            if baseline_proc.returncode != 0:
                baseline_failures.append(baseline_proc.stdout[:200])

            stages.append(
                StageResult(
                    stage=StageName.BASELINE,
                    outcome=StageOutcome.PASS if not baseline_failures else StageOutcome.FAIL,
                    duration_ms=base_duration,
                    summary=f"Baseline finished with exit code {baseline_proc.returncode}",
                )
            )

            # Stage 2: Apply patch
            start_t = time.perf_counter()
            patch_file = ws / "temp_patch.diff"
            patch_file.write_text(proposal.diff, encoding="utf-8")

            # Try git apply
            git_apply = subprocess.run(
                ["git", "apply", "--check", str(patch_file)],
                cwd=str(ws),
                capture_output=True,
                text=True,
            )
            apply_outcome = StageOutcome.PASS if git_apply.returncode == 0 else StageOutcome.FAIL
            if git_apply.returncode == 0:
                subprocess.run(["git", "apply", str(patch_file)], cwd=str(ws), capture_output=True)

            stages.append(
                StageResult(
                    stage=StageName.GUARD,
                    outcome=apply_outcome,
                    duration_ms=int((time.perf_counter() - start_t) * 1000),
                    summary="Patch applied successfully" if apply_outcome == StageOutcome.PASS else "git apply failed",
                )
            )

            if apply_outcome == StageOutcome.FAIL:
                return ValidationReport(
                    patch_id=patch_id,
                    verdict=Verdict.NOT_VALIDATED,
                    stages=stages,
                    baseline_failures=baseline_failures,
                    new_failures=["Diff does not apply cleanly"],
                )

            # Stage 3: Patched tests
            start_t = time.perf_counter()
            patched_proc = subprocess.run(
                [sys.executable, "-m", "pytest", "-q"],
                cwd=str(ws),
                capture_output=True,
                text=True,
            )
            test_duration = int((time.perf_counter() - start_t) * 1000)
            patched_failures: list[str] = []
            if patched_proc.returncode != 0:
                patched_failures.append(patched_proc.stdout[:200])

            stages.append(
                StageResult(
                    stage=StageName.TESTS,
                    outcome=StageOutcome.PASS if not patched_failures else StageOutcome.FAIL,
                    duration_ms=test_duration,
                    summary=f"Tests finished with exit code {patched_proc.returncode}",
                )
            )

            # Stage 4: Re-scan
            start_t = time.perf_counter()
            rescan_findings = self.scanner.scan_path(ws)
            rescan_duration = int((time.perf_counter() - start_t) * 1000)

            stages.append(
                StageResult(
                    stage=StageName.RESCAN,
                    outcome=StageOutcome.PASS,
                    duration_ms=rescan_duration,
                    summary=f"Re-scan found {len(rescan_findings)} findings",
                )
            )

            # Determine final verdict
            verdict, new_failures, new_findings = determine_verdict(
                patch_id=patch_id,
                baseline_failures=baseline_failures,
                patched_failures=patched_failures,
                target_finding=target_finding,
                rescan_findings=rescan_findings,
            )

            return ValidationReport(
                patch_id=patch_id,
                verdict=verdict,
                stages=stages,
                baseline_failures=baseline_failures,
                new_failures=new_failures,
                new_findings=new_findings,
            )

