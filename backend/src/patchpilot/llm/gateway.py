from __future__ import annotations

import hashlib
import json
from sqlalchemy.orm import Session

from patchpilot.config import get_settings
from patchpilot.db.models.llm import LLMCallModel
from patchpilot.llm.providers.base import BaseLLMProvider
from patchpilot.llm.providers.fake import FakeLLMProvider
from patchpilot.llm.providers.ollama import OllamaProvider
from patchpilot.llm.providers.openai_compat import OpenAICompatProvider
from patchpilot.llm.types import LLMRequest, LLMResponse
from patchpilot.observability import LLM_CALL_LATENCY, LLM_TOKENS_TOTAL


class LLMGateway:
    """The single entry point for all LLM calls in PatchPilot."""

    def __init__(self, provider: BaseLLMProvider | None = None) -> None:
        if provider:
            self.provider = provider
        else:
            settings = get_settings()
            if settings.default_model == "fake" or not settings.ollama_base_url:
                self.provider = FakeLLMProvider()
            else:
                self.provider = OllamaProvider()

    def complete(self, request: LLMRequest, db: Session | None = None) -> LLMResponse:
        # 1. Compute prompt content hash
        all_text = "".join(m.content for m in request.messages)
        prompt_hash = hashlib.sha256(all_text.encode("utf-8")).hexdigest()

        # 2. Invoke provider
        response = self.provider.complete(request)

        # 3. Track metrics
        LLM_CALL_LATENCY.labels(
            provider=response.provider,
            model=response.model,
            purpose=request.purpose,
        ).observe(response.latency_ms / 1000.0)

        LLM_TOKENS_TOTAL.labels(model=response.model, direction="in").inc(response.tokens_in)
        LLM_TOKENS_TOTAL.labels(model=response.model, direction="out").inc(response.tokens_out)

        # 4. Record to llm_calls table if DB session provided
        if db is not None:
            try:
                call_log = LLMCallModel(
                    job_id=request.job_id,
                    patch_id=request.patch_id,
                    provider=response.provider,
                    model=response.model,
                    prompt_version=request.prompt_version,
                    params={
                        "temperature": request.temperature,
                        "max_tokens": request.max_tokens,
                        "purpose": request.purpose,
                    },
                    prompt_hash=prompt_hash,
                    tokens_in=response.tokens_in,
                    tokens_out=response.tokens_out,
                    latency_ms=response.latency_ms,
                    cost=0.0,
                )
                db.add(call_log)
                db.flush()
            except Exception:
                pass

        return response

