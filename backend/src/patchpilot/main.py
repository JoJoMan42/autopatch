from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import patchpilot
from patchpilot.api.error_handlers import domain_error_handler
from patchpilot.api.router import api_router
from patchpilot.config import get_settings
from patchpilot.errors import DomainError
from patchpilot.logging_config import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings = get_settings()
    setup_logging(settings.log_level)
    yield


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="PatchPilot API",
        description="AI-Assisted Secure Code Repair Platform REST and WebSocket API",
        version=patchpilot.__version__,
        lifespan=lifespan,
    )

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Global domain error handler
    app.add_exception_handler(DomainError, domain_error_handler)  # type: ignore

    # Mount API v1 router
    app.include_router(api_router)

    return app


app = create_app()

