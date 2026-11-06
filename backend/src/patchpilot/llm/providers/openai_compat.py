from __future__ import annotations

import time
import httpx

from patchpilot.config import get_settings
from patchpilot.errors import ConfigError, LLMUnavailableError
from patchpilot.llm.providers.base import BaseLLMProvider
from patchpilot.llm.types import LLMRequest, LLMResponse


class OpenAICompatProvider(BaseLLMProvider):
    @property
    def provider_name(self) -> str:
        return "openai_compat"

    def complete(self, request: LLMRequest) -> LLMResponse:
        settings = get_settings()

        if not settings.allow_hosted_llm and "localhost" not in settings.openai_compat_base_url and "127.0.0.1" not in settings.openai_compat_base_url:
            raise ConfigError(
                "Hosted LLM calls are disabled by default. Set ALLOW_HOSTED_LLM=true to enable."
            )

        if not settings.openai_compat_base_url:
            raise ConfigError("OPENAI_COMPAT_BASE_URL is not configured.")

        url = f"{settings.openai_compat_base_url.rstrip('/')}/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.openai_compat_api_key or 'none'}",
            "Content-Type": "application/json",
        }

        messages = [{"role": m.role, "content": m.content} for m in request.messages]
        payload = {
            "model": request.model or settings.default_model,
            "messages": messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
        }

        start_time = time.perf_counter()
        try:
            with httpx.Client(timeout=120.0) as client:
                res = client.post(url, json=payload, headers=headers)
                res.raise_for_status()
                data = res.json()
        except Exception as e:
            raise LLMUnavailableError(f"OpenAI-compatible endpoint failed: {e}") from e

        latency = int((time.perf_counter() - start_time) * 1000)
        choice = data.get("choices", [{}])[0]
        content = choice.get("message", {}).get("content", "")
        usage = data.get("usage", {})

        return LLMResponse(
            text=content,
            model=data.get("model", request.model or "unknown"),
            provider=self.provider_name,
            tokens_in=usage.get("prompt_tokens", 0),
            tokens_out=usage.get("completion_tokens", 0),
            latency_ms=latency,
            finish_reason=choice.get("finish_reason", "stop"),
        )

