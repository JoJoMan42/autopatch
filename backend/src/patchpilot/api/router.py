from __future__ import annotations

from fastapi import APIRouter

from patchpilot.api.routes.auth import router as auth_router
from patchpilot.api.routes.findings import router as findings_router
from patchpilot.api.routes.health import router as health_router
from patchpilot.api.routes.patches import router as patches_router
from patchpilot.api.routes.projects import router as projects_router
from patchpilot.api.routes.repair import router as repair_router
from patchpilot.api.routes.reviews import router as reviews_router
from patchpilot.api.routes.scans import router as scans_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(projects_router)
api_router.include_router(scans_router)
api_router.include_router(findings_router)
api_router.include_router(repair_router)
api_router.include_router(patches_router)
api_router.include_router(reviews_router)

