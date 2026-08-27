"""Validated Redis infrastructure configuration."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlsplit

from pydantic import SecretStr

from app.core.config import Settings, settings
from app.infrastructure.redis.exceptions import RedisConfigurationError


@dataclass(frozen=True, slots=True)
class RedisConfig:
    """Connection settings used to construct the shared Redis client."""

    url: SecretStr
    socket_connect_timeout: float = 5.0
    socket_timeout: float = 5.0
    health_check_interval: int = 30
    retry_count: int = 3

    @classmethod
    def from_settings(cls, application_settings: Settings = settings) -> "RedisConfig":
        """Build validated Redis configuration from application settings.

        Args:
            application_settings: Environment-backed application configuration.

        Returns:
            A validated Redis configuration with the URL protected as a secret.

        Raises:
            RedisConfigurationError: If the URL is empty or not redis/rediss.
        """
        raw_url = str(application_settings.redis_url).strip()
        parsed = urlsplit(raw_url)
        if parsed.scheme not in {"redis", "rediss"} or not parsed.hostname:
            raise RedisConfigurationError(
                "REDIS_URL must be a valid redis:// or rediss:// TCP URL."
            )
        return cls(url=SecretStr(raw_url))
