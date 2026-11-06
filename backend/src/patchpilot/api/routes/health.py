from __future__ import annotations

from fastapi import APIRouter, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

import patchpilot

router = APIRouter(tags=["Health & Monitoring"])


@router.get("/health")
def health_check() -> dict[str, str]:
    return {
        "status": "healthy",
        "version": patchpilot.__version__,
    }


@router.get("/metrics")
def metrics_endpoint() -> Response:
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

