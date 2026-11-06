from __future__ import annotations

from typing import Any


class DomainError(Exception):
    """Base class for all domain exceptions in PatchPilot."""

    http_status: int = 500
    problem_type: str = "internal-error"

    def __init__(self, message: str, *, detail: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.detail = detail or {}


class AuthenticationError(DomainError):
    http_status = 401
    problem_type = "unauthenticated"


class PermissionDeniedError(DomainError):
    http_status = 403
    problem_type = "forbidden"


class NotFoundError(DomainError):
    http_status = 404
    problem_type = "not-found"


class ValidationFailed(DomainError):
    http_status = 422
    problem_type = "validation-error"


class InvalidStateError(DomainError):
    http_status = 409
    problem_type = "invalid-state"


class ApprovalRequiredError(DomainError):
    http_status = 409
    problem_type = "approval-required"


class ConflictError(DomainError):
    http_status = 409
    problem_type = "version-conflict"


class RateLimitedError(DomainError):
    http_status = 429
    problem_type = "rate-limited"


class SandboxUnavailableError(DomainError):
    http_status = 503
    problem_type = "sandbox-unavailable"


class LLMUnavailableError(DomainError):
    http_status = 503
    problem_type = "llm-unavailable"


class ConfigError(DomainError):
    http_status = 500
    problem_type = "configuration-error"

