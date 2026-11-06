from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse

from patchpilot.errors import DomainError
from patchpilot.schemas.common import ProblemDetail


def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
    """Map domain exceptions to RFC 7807 problem details response."""
    problem = ProblemDetail(
        type=f"https://patchpilot.dev/errors/{exc.problem_type}",
        title=exc.problem_type.replace("-", " ").title(),
        status=exc.http_status,
        detail=str(exc.message),
        instance=request.url.path,
        invalid_params=exc.detail.get("invalid_params") if exc.detail else None,
    )
    return JSONResponse(
        status_code=exc.http_status,
        content=problem.model_dump(exclude_none=True),
        headers={"Content-Type": "application/problem+json"},
    )

