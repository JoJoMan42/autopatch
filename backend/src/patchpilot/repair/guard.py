from __future__ import annotations

import re
from patchpilot.config import get_settings
from patchpilot.errors import ValidationFailed
from patchpilot.observability import GUARD_VIOLATIONS_TOTAL
from patchpilot.repair.ast_guard import check_ast_guard
from patchpilot.repair.diff_utils import (
    count_changed_lines,
    extract_changed_files_from_diff,
    validate_diff_structure,
)
from patchpilot.schemas.pipeline import GuardIssue, GuardReport

SUPPRESSION_REGEX = re.compile(
    r"(#\s*(?:nosec|nosemgrep|noqa(?::\s*S\d+)?|fmt:\s*off))",
    re.IGNORECASE,
)

FORBIDDEN_PATH_SUBSTRINGS = [
    ".github",
    ".gitlab-ci",
    "dockerfile",
    "docker-compose",
    "requirements",
    "poetry.lock",
    "pyproject.toml",
]


class PatchGuard:
    """Deterministic static gate verifying scope, size, suppression markers, and AST compliance."""

    def __init__(
        self,
        max_files: int | None = None,
        max_changed_lines: int | None = None,
    ) -> None:
        settings = get_settings()
        self.max_files = max_files or settings.guard_max_files
        self.max_changed_lines = max_changed_lines or settings.guard_max_changed_lines

    def verify_patch(
        self,
        diff_text: str,
        expected_target_file: str,
        cwe: str | None = None,
        patched_file_content: str | None = None,
        allowed_imports: set[str] | None = None,
    ) -> GuardReport:
        issues: list[GuardIssue] = []

        # 1. Structural diff checks
        try:
            validate_diff_structure(diff_text)
        except ValidationFailed as e:
            return GuardReport(
                ok=False,
                issues=[GuardIssue(code="MALFORMED_DIFF", message=str(e))],
                changed_files=[],
                changed_lines=0,
            )

        changed_files = extract_changed_files_from_diff(diff_text)
        changed_lines = count_changed_lines(diff_text)

        # 2. Scope check: max files
        if len(changed_files) > self.max_files:
            issues.append(
                GuardIssue(
                    code="SCOPE_TOO_MANY_FILES",
                    message=f"Diff modifies {len(changed_files)} files, exceeding limit of {self.max_files}",
                )
            )

        # 3. Scope check: expected target file
        norm_expected = expected_target_file.replace("\\", "/").lower()
        for f in changed_files:
            norm_f = f.replace("\\", "/").lower()
            if norm_f != norm_expected:
                issues.append(
                    GuardIssue(
                        code="OUT_OF_SCOPE_FILE",
                        message=f"Diff modifies unauthorized file '{f}', expected '{expected_target_file}'",
                        file_path=f,
                    )
                )

        # 4. Protected configuration / CI files
        for f in changed_files:
            lower_f = f.lower()
            for forbidden in FORBIDDEN_PATH_SUBSTRINGS:
                if forbidden in lower_f:
                    issues.append(
                        GuardIssue(
                            code="PROTECTED_FILE_MODIFIED",
                            message=f"Modification to build/CI/dependency file is forbidden: {f}",
                            file_path=f,
                        )
                    )

        # 5. Changed lines limit
        if changed_lines > self.max_changed_lines:
            issues.append(
                GuardIssue(
                    code="DIFF_TOO_LARGE",
                    message=f"Diff contains {changed_lines} changed lines, exceeding maximum limit of {self.max_changed_lines}",
                )
            )

        # 6. Suppression comments check
        for line_no, line in enumerate(diff_text.splitlines(), 1):
            if line.startswith("+") and not line.startswith("+++"):
                match = SUPPRESSION_REGEX.search(line)
                if match:
                    issues.append(
                        GuardIssue(
                            code="SUPPRESSION_COMMENT_BANNED",
                            message=f"Cosmetic fix rejected: suppression comment '{match.group(1)}' added at diff line {line_no}",
                            line=line_no,
                        )
                    )

        # 7. AST structural guard on patched code if content provided
        if patched_file_content:
            ast_issues = check_ast_guard(
                patched_source=patched_file_content,
                file_path=expected_target_file,
                project_allowed_imports=allowed_imports,
            )
            issues.extend(ast_issues)

        # Record metrics for any detected violations
        for issue in issues:
            GUARD_VIOLATIONS_TOTAL.labels(code=issue.code, cwe=cwe or "UNKNOWN").inc()

        is_ok = len(issues) == 0
        return GuardReport(
            ok=is_ok,
            issues=issues,
            changed_files=changed_files,
            changed_lines=changed_lines,
        )

