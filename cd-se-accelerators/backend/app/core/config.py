"""Centralized, environment-backed application settings for AI BA Accelerator."""

import os
from pathlib import Path
from functools import lru_cache
from typing import List, Union

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application Settings managed via Pydantic BaseSettings and .env configuration."""

    app_name: str = Field(default="AI BA Accelerator", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    debug: bool = Field(default=True, alias="DEBUG")
    api_prefix: str = Field(default="/api/v1", alias="API_PREFIX")
    api_version: str = Field(default="v1", alias="API_VERSION")
    secret_key: str = Field(default="dev-secret-key-change-in-production-32bytes-min!", alias="SECRET_KEY")

    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")

    # Database Settings (PostgreSQL or SQLite fallback)
    database_url: str = Field(
        default="sqlite:///./cd_se_accelerators.db", alias="DATABASE_URL"
    )
    db_echo: bool = Field(default=False, alias="DB_ECHO")

    # LLM Settings
    llm_provider: str = Field(default="groq", alias="LLM_PROVIDER")
    groq_api_key: str = Field(default="", alias="GROQ_API_KEY")
    groq_model: str = Field(default="llama-3.3-70b-versatile", alias="GROQ_MODEL")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o", alias="OPENAI_MODEL")
    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-1.5-pro", alias="GEMINI_MODEL")

    # Logging Settings
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_format: str = Field(default="console", alias="LOG_FORMAT")
    log_file_path: str = Field(default="logs/app.log", alias="LOG_FILE_PATH")

    # CORS Settings
    cors_origins: Union[List[str], str] = Field(
        default=["http://localhost:5173", "http://localhost:3000", "http://localhost:5000"],
        alias="CORS_ORIGINS",
    )

    # Workspace & Outputs Settings
    workspace_root: str = Field(default=str(Path(__file__).resolve().parent.parent.parent.parent / "workspace"), alias="WORKSPACE_ROOT")
    outputs_root: str = Field(default=str(Path(__file__).resolve().parent.parent.parent.parent / "outputs"), alias="OUTPUTS_ROOT")
    configs_root: str = Field(default=str(Path(__file__).resolve().parent.parent.parent.parent / "configs"), alias="CONFIGS_ROOT")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                import json
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings singleton."""
    return Settings()
