from datetime import UTC, datetime
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field
from sqlalchemy import text

from app.core.config import get_settings
from app.core.errors import AppError
from app.db.redis import redis_client
from app.db.session import engine

router = APIRouter()
settings = get_settings()


class HealthResponse(BaseModel):
    status: Literal["ok", "ready"]
    service: str
    version: str
    environment: str
    timestamp: datetime
    checks: dict[str, str] = Field(default_factory=dict)


def _base_response(status: Literal["ok", "ready"], checks: dict[str, str]) -> HealthResponse:
    return HealthResponse(
        status=status,
        service=settings.project_name,
        version=settings.app_version,
        environment=settings.environment,
        timestamp=datetime.now(UTC),
        checks=checks,
    )


@router.get("/live", response_model=HealthResponse, summary="Liveness probe")
async def liveness() -> HealthResponse:
    return _base_response("ok", {"application": "ok"})


@router.get("/ready", response_model=HealthResponse, summary="Readiness probe")
async def readiness() -> HealthResponse:
    checks = {
        "application": "ok",
        "database": "not_checked",
        "redis": "not_checked",
    }

    if settings.healthcheck_database:
        try:
            async with engine.connect() as connection:
                await connection.execute(text("SELECT 1"))
        except Exception as exc:
            raise AppError(
                code="database_unavailable",
                message="Database readiness check failed",
                status_code=503,
            ) from exc
        checks["database"] = "ok"

    if settings.healthcheck_redis:
        try:
            await redis_client.ping()
        except Exception as exc:
            raise AppError(
                code="redis_unavailable",
                message="Redis readiness check failed",
                status_code=503,
            ) from exc
        checks["redis"] = "ok"

    return _base_response("ready", checks)
