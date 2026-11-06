from __future__ import annotations

from typing import Any
from patchpilot.schemas.pipeline import ContextSnippet


def estimate_tokens(text: str) -> int:
    """Fast approximation of token count (~4 characters per token)."""
    if not text:
        return 0
    return max(1, len(text) // 4)


class TokenBudgetManager:
    """Manages allocation and truncation across prompt layers for a given context window limit."""

    def __init__(self, total_context_limit: int = 16_000, reserved_response_tokens: int = 3_000) -> None:
        self.total_limit = total_context_limit
        self.reserved_response = reserved_response_tokens
        self.available_prompt_tokens = total_context_limit - reserved_response_tokens

    def fit_snippets(
        self,
        slice_text: str,
        snippets: list[ContextSnippet],
        cwe_guidance: str = "",
    ) -> tuple[list[ContextSnippet], str, int]:
        """Fit slice, snippets, and guidance into token budget, truncating lower priority items first."""
        base_tokens = estimate_tokens(slice_text) + 1000  # including system prompt base
        guidance_tokens = estimate_tokens(cwe_guidance)

        remaining = self.available_prompt_tokens - base_tokens - guidance_tokens
        if remaining < 0:
            # Truncate guidance if needed
            cwe_guidance = cwe_guidance[: max(100, (self.available_prompt_tokens - base_tokens) * 4)]
            remaining = 500

        # Priority ordering for snippets:
        # 1. callers / callees / helper
        # 2. example
        # 3. similar
        priority_map = {
            "helper": 1,
            "callers": 2,
            "callees": 3,
            "example": 4,
            "similar": 5,
            "cwe_guidance": 6,
        }

        sorted_snippets = sorted(
            snippets,
            key=lambda s: (priority_map.get(s.kind, 99), -(s.score or 0.0)),
        )

        accepted_snippets: list[ContextSnippet] = []
        used_tokens = base_tokens + estimate_tokens(cwe_guidance)

        for snip in sorted_snippets:
            snip_tokens = estimate_tokens(snip.text)
            if used_tokens + snip_tokens <= self.available_prompt_tokens:
                accepted_snippets.append(snip)
                used_tokens += snip_tokens

        return accepted_snippets, cwe_guidance, used_tokens

