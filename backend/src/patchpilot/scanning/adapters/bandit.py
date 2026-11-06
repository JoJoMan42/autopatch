from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from patchpilot.constants import Severity
from patchpilot.scanning.adapters.base import BaseScannerAdapter
from patchpilot.scanning.cwe_mapper import map_rule_to_cwe
from patchpilot.scanning.fingerprint import generate_finding_fingerprint
from patchpilot.schemas.pipeline import NormalizedFinding


class BanditAdapter(BaseScannerAdapter):
    @property
    def scanner_name(self) -> str:
        return "bandit"

    def scan_path(self, target_path: Path) -> list[NormalizedFinding]:
        cmd = [
            sys.executable,
            "-m",
            "bandit",
            "-r",
            str(target_path),
            "-f",
            "json",
            "-q",
        ]

        # Note: Never use shell=True per project security specification
        proc = subprocess.run(cmd, capture_output=True, text=True)
        findings: list[NormalizedFinding] = []

        if not proc.stdout:
            return findings

        try:
            data = json.loads(proc.stdout)
        except json.JSONDecodeError:
            return findings

        for result in data.get("results", []):
            rule_id = result.get("test_id", "UNKNOWN")
            test_name = result.get("test_name", "")
            raw_cwe = result.get("issue_cwe", {})
            reported_cwe = f"CWE-{raw_cwe.get('id')}" if raw_cwe.get("id") else None

            cwe = map_rule_to_cwe(rule_id, reported_cwe) or map_rule_to_cwe(test_name)

            sev_str = result.get("issue_severity", "MEDIUM").lower()
            if sev_str == "high":
                severity = Severity.HIGH
            elif sev_str == "low":
                severity = Severity.LOW
            else:
                severity = Severity.MEDIUM

            filename = result.get("filename", "")
            line_no = result.get("line_number", 1)
            line_range = result.get("line_range", [line_no])
            end_line = line_range[-1] if line_range else line_no
            code_text = result.get("code", "")
            message = result.get("issue_text", "")

            fingerprint = generate_finding_fingerprint(filename, rule_id, code_text)

            findings.append(
                NormalizedFinding(
                    scanner=self.scanner_name,
                    rule_id=rule_id,
                    cwe=cwe,
                    severity=severity,
                    file_path=filename.replace("\\", "/"),
                    start_line=line_no,
                    end_line=end_line,
                    message=message,
                    fingerprint=fingerprint,
                    raw=result,
                )
            )

        return findings

