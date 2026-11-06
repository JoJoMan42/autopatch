from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field


class Message(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class LLMRequest(BaseModel):
    purpose: Literal["repair", "feedback", "security_test", "judge", "summary"]
    messages: list[Message]
    model: str | None = None  # None means DEFAULT_MODEL
    temperature: float = 0.1
    max_tokens: int = 2048
    json_schema: dict[str, Any] | None = None
    seed: int | None = None
    job_id: str | None = None
    patch_id: str | None = None
    prompt_version: str = "v1"


class LLMResponse(BaseModel):
    text: str
    model: str
    provider: str
    tokens_in: int
    tokens_out: int
    latency_ms: int
    finish_reason: str

