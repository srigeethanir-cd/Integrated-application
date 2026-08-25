from functools import lru_cache
import logging
from pathlib import Path

from pydantic import Field, PostgresDsn, RedisDsn, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

SUPPORTED_CEREBRAS_MODELS = frozenset(
    {
        "gpt-oss-120b",
        "zai-glm-4.7",
        "qwen-3-235b-a22b-instruct-2507",
    }
)


class LLMProviderConfigurationError(RuntimeError):
    """Raised when an LLM provider is configured with an unsupported model."""


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        validate_default=True,
    )

    app_name: str = "Test Case Accelerator"
    app_version: str = "0.1.0"
    debug: bool = False
    database_url: PostgresDsn = Field(
        default=(
            "postgresql+psycopg://postgres:postgres@localhost:5432/"
            "test_case_accelerator"
        )
    )
    redis_url: RedisDsn = Field(default="redis://localhost:6379/0")
    stage3_provider_cache_ttl_seconds: int = Field(default=21_600, gt=0)
    stage3_enrichment_cache_ttl_seconds: int = Field(default=21_600, gt=0)
    runtime_preparation_cache_ttl_seconds: int = Field(default=43_200, gt=0)
    pipeline_checkpoint_cache_ttl_seconds: int = Field(default=43_200, gt=0)
    groq_api_key: SecretStr | None = Field(default=None, repr=False)
    groq_model: str = Field(default="openai/gpt-oss-20b", min_length=1)
    cerebras_api_key: SecretStr | None = Field(default=None, repr=False)
    cerebras_model: str = Field(default="gpt-oss-120b", min_length=1)
    primary_llm_provider: str = Field(default="groq", pattern="^(groq|cerebras)$")
    fallback_llm_provider: str = Field(default="cerebras", pattern="^(groq|cerebras)$")
    provider_failover_threshold_seconds: float = Field(default=30.0, ge=0)
    max_provider_retries: int = Field(default=2, ge=0, le=5)
    enable_provider_failover: bool = True
    enable_stage3_cache: bool = True
    groq_model_max_output_tokens: int = Field(default=65_536, gt=0)
    groq_tokens_per_minute: int = Field(default=8_000, gt=0)
    groq_requests_per_minute: int = Field(default=30, gt=0)
    cerebras_model_max_output_tokens: int = Field(default=40_960, gt=0)
    cerebras_tokens_per_minute: int = Field(default=60_000, gt=0)
    cerebras_requests_per_minute: int = Field(default=30, gt=0)
    llm_token_preflight_reserve: int = Field(default=256, ge=0)
    stage3_completion_estimation_safety_margin: float = Field(
        default=0.2, ge=0, le=1
    )
    code_understanding_max_file_characters: int = Field(default=2_500, gt=0)
    code_understanding_max_total_characters: int = Field(default=10_000, gt=0)
    test_verification_max_provider_attempts: int = Field(default=3, ge=1, le=5)
    test_verification_retry_base_delay: float = Field(default=0.25, ge=0)
    test_verification_max_retry_delay: float = Field(default=2.0, ge=0)
    test_verification_rule_confidence_threshold: float = Field(
        default=0.8, ge=0, le=1
    )
    test_generation_max_completion_tokens: int = Field(default=16_384, ge=4_096, le=40_000)
    test_generation_batch_max_functions: int = Field(default=4, ge=1, le=20)
    test_generation_estimated_tokens_per_case: int = Field(default=650, ge=100)
    test_generation_safe_output_tokens: int = Field(default=12_000, ge=1_000, le=32_000)
    test_quality_threshold: float = Field(default=80.0, ge=0, le=100)
    test_quality_max_iterations: int = Field(default=2, ge=1, le=2)
    test_quality_minimum_improvement_delta: float = Field(
        default=2.0, ge=0, le=100
    )
    storage_root: Path = Field(default=Path("storage/projects"))
    max_upload_size_bytes: int = Field(default=104_857_600, gt=0)
    max_zip_entries: int = Field(default=10_000, gt=0)
    max_zip_total_uncompressed_size_bytes: int = Field(
        default=1_073_741_824,
        gt=0,
    )
    max_zip_file_uncompressed_size_bytes: int = Field(
        default=104_857_600,
        gt=0,
    )
    max_zip_compression_ratio: float = Field(default=100.0, gt=0)
    semgrep_executable: str = Field(default="semgrep", min_length=1)
    semgrep_config: str = Field(default="p/default", min_length=1)
    semgrep_explicit_config: str | None = None
    semgrep_metrics_enabled: bool = False
    semgrep_timeout_seconds: int = Field(default=300, gt=0)
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://localhost:5173",
        ]
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()


def validate_llm_provider_configuration(config: Settings = settings) -> None:
    """Validate provider-specific models before accepting application traffic."""
    logger.info(
        "Configured LLM provider=%s model=%s",
        config.primary_llm_provider,
        config.groq_model,
    )
    if config.cerebras_model not in SUPPORTED_CEREBRAS_MODELS:
        supported = ", ".join(sorted(SUPPORTED_CEREBRAS_MODELS))
        raise LLMProviderConfigurationError(
            "Invalid Cerebras model configuration "
            f"'{config.cerebras_model}'. Supported public model IDs: {supported}"
        )
    logger.info(
        "Configured LLM provider=%s model=%s",
        config.fallback_llm_provider,
        config.cerebras_model,
    )
