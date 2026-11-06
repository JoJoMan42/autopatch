from __future__ import annotations

from pathlib import Path
from typing import Any

from patchpilot.context.knowledge_base import get_cwe_guidance
from patchpilot.context.slicer import slice_code_at_finding
from patchpilot.context.token_budget import TokenBudgetManager, estimate_tokens
from patchpilot.schemas.pipeline import ContextBundle, ContextSnippet, NormalizedFinding


def build_finding_context(
    finding: NormalizedFinding,
    source_code: str,
    callers: list[str] | None = None,
    callees: list[str] | None = None,
    retrieved_snippets: list[ContextSnippet] | None = None,
    budget_limit: int = 16_000,
) -> ContextBundle:
    """Assemble the rich prompt context bundle within token budget."""
    code_slice = slice_code_at_finding(
        file_path=finding.file_path,
        source=source_code,
        flagged_line=finding.start_line,
    )

    guidance_text = get_cwe_guidance(finding.cwe)
    all_snippets: list[ContextSnippet] = list(retrieved_snippets or [])

    if callers:
        all_snippets.append(
            ContextSnippet(
                kind="callers",
                file_path=finding.file_path,
                text=f"Callers of {code_slice.function_name}: {', '.join(callers)}",
            )
        )

    if callees:
        all_snippets.append(
            ContextSnippet(
                kind="callees",
                file_path=finding.file_path,
                text=f"Callees of {code_slice.function_name}: {', '.join(callees)}",
            )
        )

    all_snippets.append(
        ContextSnippet(
            kind="cwe_guidance",
            text=guidance_text,
        )
    )

    budget_mgr = TokenBudgetManager(total_context_limit=budget_limit)
    fitted_snippets, _, total_tokens = budget_mgr.fit_snippets(
        slice_text=code_slice.source,
        snippets=all_snippets,
        cwe_guidance=guidance_text,
    )

    return ContextBundle(
        finding_id=finding.fingerprint,
        cwe=finding.cwe,
        code_slice=code_slice,
        snippets=fitted_snippets,
        token_estimate=total_tokens,
        retrieved_chunk_ids=[s.chunk_id for s in fitted_snippets if s.chunk_id],
    )

