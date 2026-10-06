from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging
from app.core.middleware import register_http_middleware
from app.db.session import engine

settings = get_settings()
configure_logging(settings.log_level, settings.log_json)
logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    logger.info(
        "application_started",
        service=settings.project_name,
        version=settings.app_version,
        environment=settings.environment,
    )
    try:
        yield
    finally:
        await engine.dispose()
        logger.info("application_stopped", service=settings.project_name)


def create_application() -> FastAPI:
    app = FastAPI(
        title=settings.project_name,
        version=settings.app_version,
        description="FactoryPilot 智造协同决策平台主业务 API",
        debug=settings.debug,
        docs_url="/docs" if settings.docs_enabled else None,
        redoc_url="/redoc" if settings.docs_enabled else None,
        openapi_url="/openapi.json" if settings.docs_enabled else None,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_http_middleware(app)
    register_exception_handlers(app)
    app.include_router(api_router, prefix=settings.api_v1_prefix)

    @app.get("/", tags=["meta"])
    async def service_info() -> dict[str, str]:
        return {
            "service": settings.project_name,
            "version": settings.app_version,
            "environment": settings.environment,
            "docs": "/docs" if settings.docs_enabled else "disabled",
        }

    return app


app = create_application()
