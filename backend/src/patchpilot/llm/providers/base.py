from __future__ import annotations

from abc import ABC, abstractmethod
from patchpilot.llm.types import LLMRequest, LLMResponse


class BaseLLMProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Identifier for this provider."""

    @abstractmethod
    def complete(self, request: LLMRequest) -> LLMResponse:
        """Execute completion request and return standardized LLMResponse."""

