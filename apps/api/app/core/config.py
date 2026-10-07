from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

API_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=API_DIR / ".env",
        env_prefix="FACTORYPILOT_",
        case_sensitive=False,
        extra="ignore",
    )

    project_name: str = "FactoryPilot API"
    app_version: str = "0.1.0"
    environment: Literal["development", "test", "staging", "production"] = "development"
    debug: bool = False
    docs_enabled: bool = True
    api_v1_prefix: str = "/api/v1"

    database_url: str = (
        "postgresql+asyncpg://factorypilot:factorypilot@127.0.0.1:5432/factorypilot"
    )
    database_pool_size: int = 5
    database_max_overflow: int = 10
    redis_url: str = "redis://127.0.0.1:6379/0"

    jwt_secret_key: str = "factorypilot-development-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_issuer: str = "factorypilot"
    jwt_audience: str = "factorypilot-api"
    access_token_minutes: int = 15
    refresh_token_days: int = 7

    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:8001", "http://127.0.0.1:8001"]
    )

    log_level: str = "INFO"
    log_json: bool = False
    healthcheck_database: bool = True
    healthcheck_redis: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
