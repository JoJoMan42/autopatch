from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from patchpilot.schemas.pipeline import NormalizedFinding


class BaseScannerAdapter(ABC):
    @property
    @abstractmethod
    def scanner_name(self) -> str:
        """Name of the scanner."""

    @abstractmethod
    def scan_path(self, target_path: Path) -> list[NormalizedFinding]:
        """Execute or invoke scanner against the target path and return findings."""

