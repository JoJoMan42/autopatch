from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from patchpilot.constants import Severity
from patchpilot.scanning.cwe_mapper import map_rule_to_cwe
from patchpilot.scanning.fingerprint import generate_finding_fingerprint
from patchpilot.schemas.pipeline import NormalizedFinding


def parse_sarif_content(sarif_data: dict[str, Any], default_scanner: str = "sarif") -> list[NormalizedFinding]:
    """Parse SARIF 2.1.0 data and return normalized findings list."""
    findings: list[NormalizedFinding] = []

    for run in sarif_data.get("runs", []):
        tool_driver = run.get("tool", {}).get("driver", {})
        scanner_name = tool_driver.get("name", default_scanner)

        # Build rule dictionary for quick lookup of help/CWE
        rules_dict: dict[str, Any] = {}
        for r in tool_driver.get("rules", []):
            rule_id = r.get("id")
            if rule_id:
                rules_dict[rule_id] = r

        for res in run.get("results", []):
            rule_id = res.get("ruleId", "UNKNOWN_RULE")
            rule_info = rules_dict.get(rule_id, {})
            message = res.get("message", {}).get("text", "")

            # Level mapping
            level = res.get("level", "warning").lower()
            if level == "error":
                severity = Severity.HIGH
            elif level == "note":
                severity = Severity.LOW
            else:
                severity = Severity.MEDIUM

            # Check rule tags / relationships for CWE
            reported_cwe = None
            for tag in rule_info.get("properties", {}).get("tags", []):
                if "cwe-" in tag.lower():
                    reported_cwe = tag.upper()
                    break

            cwe = map_rule_to_cwe(rule_id, reported_cwe)

            # Location extraction
            locations = res.get("locations", [])
            file_path = "unknown"
            start_line = 1
            end_line = 1
            code_snippet = None

            if locations:
                phys = locations[0].get("physicalLocation", {})
                uri = phys.get("artifactLocation", {}).get("uri", "")
                if uri:
                    file_path = uri.replace("\\", "/")

                region = phys.get("region", {})
                start_line = region.get("startLine", 1)
                end_line = region.get("endLine", start_line)
                code_snippet = region.get("snippet", {}).get("text")

            fingerprint = generate_finding_fingerprint(file_path, rule_id, code_snippet)

            findings.append(
                NormalizedFinding(
                    scanner=scanner_name,
                    rule_id=rule_id,
                    cwe=cwe,
                    severity=severity,
                    file_path=file_path,
                    start_line=start_line,
                    end_line=end_line,
                    message=message,
                    fingerprint=fingerprint,
                    raw=res,
                )
            )

    return findings


def parse_sarif_file(file_path: Path) -> list[NormalizedFinding]:
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return parse_sarif_content(data)

