from __future__ import annotations

from sqlalchemy.orm import Session

from patchpilot.llm.gateway import LLMGateway
from patchpilot.llm.output_parser import parse_patch_response
from patchpilot.llm.prompts import build_repair_prompt
from patchpilot.llm.types import LLMRequest
from patchpilot.schemas.pipeline import ContextBundle, NormalizedFinding, PatchProposal


def generate_patch(
    finding: NormalizedFinding,
    context: ContextBundle,
    gateway: LLMGateway,
    feedback: str | None = None,
    allowed_imports: set[str] | None = None,
    model: str | None = None,
    db: Session | None = None,
    job_id: str | None = None,
    patch_id: str | None = None,
) -> PatchProposal:
    """Generate a candidate patch proposal for the given finding and context bundle."""
    messages = build_repair_prompt(
        finding=finding,
        context=context,
        feedback=feedback,
        allowed_imports=allowed_imports,
    )

    req = LLMRequest(
        purpose="repair",
        messages=messages,
        model=model,
        temperature=0.1,
        max_tokens=2048,
        job_id=job_id,
        patch_id=patch_id,
        prompt_version="v1",
    )

    response = gateway.complete(req, db=db)
    return parse_patch_response(response.text)

