from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from patchpilot.scanning.adapters.base import BaseScannerAdapter
from patchpilot.scanning.sarif import parse_sarif_content
from patchpilot.schemas.pipeline import NormalizedFinding


class SemgrepAdapter(BaseScannerAdapter):
    @property
    def scanner_name(self) -> str:
        return "semgrep"

    def scan_path(self, target_path: Path) -> list[NormalizedFinding]:
        semgrep_bin = shutil.which("semgrep")
        if not semgrep_bin:
            return []

        cmd = [
            semgrep_bin,
            "scan",
            "--config",
            "auto",
            "--sarif",
            "--quiet",
            str(target_path),
        ]

        # No shell=True per project rule
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if not proc.stdout:
            return []

        try:
            sarif_data = json.loads(proc.stdout)
            return parse_sarif_content(sarif_data, default_scanner=self.scanner_name)
        except json.JSONDecodeError:
            return []

