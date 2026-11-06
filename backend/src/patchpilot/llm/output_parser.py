from __future__ import annotations

import json
import re
from patchpilot.schemas.pipeline import PatchProposal


def parse_patch_response(raw_text: str) -> PatchProposal:
    """Parse JSON patch proposal response from LLM output, extracting from markdown if needed."""
    cleaned = raw_text.strip()

    # Strip markdown fenced code blocks if present
    json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned)
    if json_match:
        cleaned = json_match.group(1).strip()

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        # Fallback: attempt to find raw JSON object boundaries { ... }
        brace_match = re.search(r"\{[\s\S]*\}", cleaned)
        if brace_match:
            try:
                data = json.loads(brace_match.group(0))
            except json.JSONDecodeError:
                return PatchProposal(
                    status="cannot_fix",
                    reason="Model response was not valid JSON",
                )
        else:
            return PatchProposal(
                status="cannot_fix",
                reason="Model did not return JSON object",
            )

    status = data.get("status", "cannot_fix")
    if status not in ("fixed", "cannot_fix"):
        status = "cannot_fix"

    confidence = data.get("confidence", 0.0)
    try:
        conf_float = float(confidence)
        conf_float = max(0.0, min(1.0, conf_float))
    except (ValueError, TypeError):
        conf_float = 0.5

    return PatchProposal(
        status=status,
        analysis=data.get("analysis", ""),
        diff=data.get("diff", "").strip(),
        explanation=data.get("explanation", ""),
        assumptions=data.get("assumptions", []),
        risks=data.get("risks", []),
        confidence=conf_float,
        reason=data.get("reason"),
    )

