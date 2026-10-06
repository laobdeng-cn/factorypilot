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
        "postgresql+asyncpg://factorypilot:factorypilot@localhost:5432/factorypilot"
    )
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://localhost:8000"]
    )

    log_level: str = "INFO"
    log_json: bool = False
    healthcheck_database: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
