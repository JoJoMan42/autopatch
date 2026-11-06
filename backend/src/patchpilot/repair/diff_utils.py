from __future__ import annotations

import re
from patchpilot.errors import ValidationFailed


def extract_changed_files_from_diff(diff_text: str) -> list[str]:
    """Extract list of target file paths modified in unified diff."""
    files = set()
    for line in diff_text.splitlines():
        if line.startswith("+++ "):
            # Example: +++ b/shop/db.py or +++ shop/db.py
            raw_path = line[4:].strip()
            if raw_path.startswith("b/"):
                raw_path = raw_path[2:]
            if raw_path != "/dev/null":
                files.add(raw_path.replace("\\", "/"))
    return sorted(files)


def validate_diff_structure(diff_text: str) -> None:
    """Validate unified diff formatting and security constraints."""
    if not diff_text or not diff_text.strip():
        raise ValidationFailed("Diff is empty")

    # Check for path traversal in diff paths
    for file_path in extract_changed_files_from_diff(diff_text):
        if ".." in file_path or file_path.startswith("/"):
            raise ValidationFailed(f"Diff targets illegal path: {file_path}")

    # Check for binary diff marker
    if "GIT binary patch" in diff_text or "Binary files" in diff_text:
        raise ValidationFailed("Binary diffs are not permitted")


def count_changed_lines(diff_text: str) -> int:
    """Count added and removed lines in a unified diff."""
    count = 0
    for line in diff_text.splitlines():
        if (line.startswith("+") and not line.startswith("+++")) or (
            line.startswith("-") and not line.startswith("---")
        ):
            count += 1
    return count

