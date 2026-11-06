from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from patchpilot.config import get_settings


class EphemeralWorkspace:
    """Manages an isolated temporary directory for applying patches and running verification."""

    def __init__(self, source_dir: Path | str) -> None:
        self.source_dir = Path(source_dir)
        self.temp_dir: Path | None = None

    def __enter__(self) -> Path:
        settings = get_settings()
        parent_dir = Path(settings.workspace_root)
        parent_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir = Path(tempfile.mkdtemp(prefix="pp_ws_", dir=parent_dir))

        # Copy source contents to temporary scratch workspace
        if self.source_dir.is_dir():
            shutil.copytree(self.source_dir, self.temp_dir, dirs_exist_ok=True)
        return self.temp_dir

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)
            self.temp_dir = None

