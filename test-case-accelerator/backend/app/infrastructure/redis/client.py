"""Singleton Redis client and connection-pool management."""

from __future__ import annotations

import logging
from functools import lru_cache

from redis import Redis
from redis.backoff import ExponentialBackoff
from redis.exceptions import ConnectionError, TimeoutError
from redis.retry import Retry
from typing import Any, Callable, TypeVar

from app.infrastructure.redis.config import RedisConfig

logger = logging.getLogger(__name__)
T = TypeVar("T")


class _LoggingRetry(Retry):
    """Redis retry policy that records reconnect attempts without credentials."""

    def call_with_retry(
        self, do: Callable[[], T], fail: Callable[[Exception], Any]
    ) -> T:
        """Run an operation and log each connection failure before retrying.

        Args:
            do: Redis operation to execute.
            fail: redis-py cleanup callback invoked after a failed attempt.

        Returns:
            The successful Redis operation result.

        Raises:
            RedisError: When configured retry attempts are exhausted.
        """
        def log_and_fail(error: Exception) -> Any:
            logger.warning(
                "Redis connection failed; automatic reconnect scheduled error=%s",
                type(error).__name__,
            )
            return fail(error)

        return super().call_with_retry(do, log_and_fail)


@lru_cache(maxsize=1)
def get_redis_client() -> Redis:
    """Return the process-wide Redis client backed by a reusable pool.

    Returns:
        A singleton redis-py client configured for retries and health checks.

    Raises:
        RedisConfigurationError: If REDIS_URL is invalid.
    """
    config = RedisConfig.from_settings()
    retry = _LoggingRetry(ExponentialBackoff(), config.retry_count)
    client = Redis.from_url(
        config.url.get_secret_value(),
        decode_responses=False,
        socket_connect_timeout=config.socket_connect_timeout,
        socket_timeout=config.socket_timeout,
        health_check_interval=config.health_check_interval,
        socket_keepalive=True,
        retry=retry,
        retry_on_error=[ConnectionError, TimeoutError],
    )
    logger.debug("Redis client initialized with pooled connections")
    return client


def close_redis_client() -> None:
    """Close the shared pool and clear the singleton client.

    Returns:
        None.
    """
    if get_redis_client.cache_info().currsize:
        get_redis_client().close()
        get_redis_client.cache_clear()
        logger.info("Redis connection pool closed")
