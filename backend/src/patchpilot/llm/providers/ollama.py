from __future__ import annotations

import time
import httpx

from patchpilot.config import get_settings
from patchpilot.errors import LLMUnavailableError
from patchpilot.llm.providers.base import BaseLLMProvider
from patchpilot.llm.types import LLMRequest, LLMResponse


class OllamaProvider(BaseLLMProvider):
    @property
    def provider_name(self) -> str:
        return "ollama"

    def complete(self, request: LLMRequest) -> LLMResponse:
        settings = get_settings()
        url = f"{settings.ollama_base_url.rstrip('/')}/api/chat"

        messages = [{"role": m.role, "content": m.content} for m in request.messages]
        payload = {
            "model": request.model or settings.default_model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": request.temperature,
                "num_predict": request.max_tokens,
            },
        }

        start_time = time.perf_counter()
        try:
            with httpx.Client(timeout=120.0) as client:
                res = client.post(url, json=payload)
                res.raise_for_status()
                data = res.json()
        except Exception as e:
            raise LLMUnavailableError(f"Ollama server connection failed: {e}") from e

        latency = int((time.perf_counter() - start_time) * 1000)
        content = data.get("message", {}).get("content", "")

        return LLMResponse(
            text=content,
            model=request.model or settings.default_model,
            provider=self.provider_name,
            tokens_in=data.get("prompt_eval_count", 0),
            tokens_out=data.get("eval_count", 0),
            latency_ms=latency,
            finish_reason="stop",
        )

