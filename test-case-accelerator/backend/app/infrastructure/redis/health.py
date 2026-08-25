"""Redis connectivity and server health reporting."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from time import perf_counter

from redis import Redis
from redis.exceptions import RedisError

from app.infrastructure.redis.client import get_redis_client

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class RedisHealth:
    """Sanitized result of a Redis connectivity check."""

    connected: bool
    latency_ms: float | None
    server_version: str | None
    error: str | None = None


def check_redis_health(client: Redis | None = None) -> RedisHealth:
    """PING Redis and return sanitized connection metadata.

    Args:
        client: Optional client override, primarily for tests.

    Returns:
        Connectivity, latency, server version when available, and safe error.
    """
    redis_client = client or get_redis_client()
    started = perf_counter()
    try:
        redis_client.ping()
        latency = round((perf_counter() - started) * 1000, 2)
        version = None
        try:
            server = redis_client.info(section="server")
            version = str(server.get("redis_version")) if server.get("redis_version") else None
        except RedisError:
            logger.debug("Redis server metadata is unavailable", exc_info=True)
        logger.info("Redis connection established latency_ms=%.2f", latency)
        return RedisHealth(True, latency, version)
    except RedisError as error:
        latency = round((perf_counter() - started) * 1000, 2)
        logger.warning(
            "Redis is unavailable; cache operations will use safe fallbacks: %s",
            type(error).__name__,
        )
        return RedisHealth(
            connected=False,
            latency_ms=latency,
            server_version=None,
            error=f"Redis unavailable ({type(error).__name__})",
        )
