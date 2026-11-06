from __future__ import annotations

from patchpilot.schemas.pipeline import ValidationReport, Verdict


def calculate_risk_score(
    report: ValidationReport | None,
    changed_lines: int,
    confidence: float,
) -> float:
    """Calculate an interpretable risk score from 0.0 (lowest risk) to 1.0 (highest risk)."""
    # Base risk starts from inverse model confidence
    risk = max(0.05, 1.0 - confidence)

    if report is not None:
        if report.verdict == Verdict.VALIDATED:
            risk *= 0.3  # Substantial risk reduction when all tests and re-scan pass cleanly
        elif report.verdict == Verdict.VALIDATED_WITH_WARNINGS:
            risk = max(risk, 0.45)
        elif report.verdict == Verdict.NOT_VALIDATED:
            risk = 0.95
        elif report.verdict == Verdict.INCONCLUSIVE:
            risk = 0.85

        if report.new_failures:
            risk = 1.0

        if report.new_findings:
            risk = max(risk, 0.9)

    # Larger diffs have inherently more blast radius risk
    if changed_lines > 25:
        risk = min(1.0, risk + 0.15)
    elif changed_lines > 10:
        risk = min(1.0, risk + 0.05)

    return round(max(0.0, min(1.0, risk)), 3)

