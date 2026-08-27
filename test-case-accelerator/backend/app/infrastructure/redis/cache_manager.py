"""Resilient JSON cache operations built on the shared Redis client."""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any
from time import perf_counter

from redis import Redis
from redis.exceptions import RedisError

from app.infrastructure.redis.client import get_redis_client
from app.infrastructure.redis.serializers import JsonSerializer
from app.infrastructure.redis.exceptions import RedisSerializationError
from app.infrastructure.redis.metrics import (
    get_cache_metrics_registry,
    key_prefix,
    stage_for_key,
)

logger = logging.getLogger(__name__)


class CacheManager:
    """Provide reusable cache operations with safe connection-error fallbacks."""

    def __init__(self, client: Redis) -> None:
        """Initialize the manager.

        Args:
            client: A configured redis-py client.
        """
        self._client = client
        self._metrics = get_cache_metrics_registry()

    def get(self, key: str) -> Any | None:
        """Read and deserialize a cached value.

        Args:
            key: Fully constructed cache key.

        Returns:
            The decoded value, or None for misses and unavailable Redis.
        """
        started = perf_counter()
        stage = stage_for_key(key)
        prefix = key_prefix(key)
        try:
            value = self._client.get(key)
            latency = (perf_counter() - started) * 1000
            if value is None:
                self._metrics.record_read(stage, hit=False, latency_ms=latency)
                logger.info(
                    "CACHE MISS stage=%s key_prefix=%s latency_ms=%.3f payload_size=0",
                    stage or "unknown", prefix, latency,
                )
                return None
            decoded = JsonSerializer.loads(value)
            self._metrics.record_read(stage, hit=True, latency_ms=latency)
            logger.info(
                "CACHE HIT stage=%s key_prefix=%s latency_ms=%.3f payload_size=%d",
                stage or "unknown", prefix, latency, len(value),
            )
            return decoded
        except (RedisError, RedisSerializationError):
            latency = (perf_counter() - started) * 1000
            self._metrics.record_error(stage)
            logger.exception(
                "CACHE ERROR stage=%s key_prefix=%s operation=get "
                "latency_ms=%.3f payload_size=0",
                stage or "unknown", prefix, latency,
            )
            return None

    def set(self, key: str, value: Any, ttl: int | None = None) -> bool:
        """Serialize and cache a value.

        Args:
            key: Fully constructed cache key.
            value: JSON-compatible value to store.
            ttl: Optional expiration in seconds.

        Returns:
            True when written, otherwise False if Redis is unavailable.

        Serialization and connection failures are logged and return False.
        """
        started = perf_counter()
        stage = stage_for_key(key)
        prefix = key_prefix(key)
        payload_size = 0
        try:
            payload = JsonSerializer.dumps(value)
            payload_size = len(payload)
            written = bool(self._client.set(key, payload, ex=ttl))
            latency = (perf_counter() - started) * 1000
            if written:
                self._metrics.record_write(stage, latency_ms=latency)
            logger.info(
                "CACHE STORE stage=%s key_prefix=%s latency_ms=%.3f "
                "payload_size=%d ttl=%s",
                stage or "unknown", prefix, latency, payload_size, ttl,
            )
            return written
        except (RedisError, RedisSerializationError):
            latency = (perf_counter() - started) * 1000
            self._metrics.record_error(stage)
            logger.exception(
                "CACHE ERROR stage=%s key_prefix=%s operation=set "
                "latency_ms=%.3f payload_size=%d",
                stage or "unknown", prefix, latency, payload_size,
            )
            return False

    def delete(self, key: str) -> bool:
        """Delete a cached value.

        Args:
            key: Fully constructed cache key.

        Returns:
            True when a key was removed; False otherwise.
        """
        try:
            deleted = int(self._client.delete(key))
            self._metrics.record_delete(stage_for_key(key), count=deleted)
            return bool(deleted)
        except RedisError:
            self._metrics.record_error(stage_for_key(key))
            logger.exception(
                "CACHE ERROR stage=%s key_prefix=%s operation=delete",
                stage_for_key(key) or "unknown", key_prefix(key),
            )
            return False

    def exists(self, key: str) -> bool:
        """Check whether a key exists.

        Args:
            key: Fully constructed cache key.

        Returns:
            True when present; False for misses or unavailable Redis.
        """
        try:
            return bool(self._client.exists(key))
        except RedisError:
            self._metrics.record_error(stage_for_key(key))
            logger.exception(
                "CACHE ERROR stage=%s key_prefix=%s operation=exists",
                stage_for_key(key) or "unknown", key_prefix(key),
            )
            return False

    def expire(self, key: str, ttl: int) -> bool:
        """Set a key expiration.

        Args:
            key: Fully constructed cache key.
            ttl: Positive expiration in seconds.

        Returns:
            True if expiration was applied; False otherwise.

        Raises:
            ValueError: If ttl is not positive.
        """
        if ttl <= 0:
            raise ValueError("Cache TTL must be positive.")
        started = perf_counter()
        try:
            result = bool(self._client.expire(key, ttl))
            if result:
                self._metrics.record_write(
                    stage_for_key(key), latency_ms=(perf_counter() - started) * 1000
                )
            return result
        except RedisError:
            self._metrics.record_error(stage_for_key(key))
            logger.exception(
                "CACHE ERROR stage=%s key_prefix=%s operation=expire",
                stage_for_key(key) or "unknown", key_prefix(key),
            )
            return False

    def increment(self, key: str) -> int | None:
        """Atomically increment an integer value.

        Args:
            key: Fully constructed counter key.

        Returns:
            The incremented value, or None when Redis is unavailable.
        """
        started = perf_counter()
        try:
            value = int(self._client.incr(key))
            self._metrics.record_write(
                stage_for_key(key), latency_ms=(perf_counter() - started) * 1000
            )
            return value
        except RedisError:
            self._metrics.record_error(stage_for_key(key))
            logger.exception(
                "CACHE ERROR stage=%s key_prefix=%s operation=increment",
                stage_for_key(key) or "unknown", key_prefix(key),
            )
            return None

    def clear_prefix(self, prefix: str) -> int:
        """Delete keys matching a prefix using non-blocking SCAN iteration.

        Args:
            prefix: Namespaced prefix without a wildcard requirement.

        Returns:
            Number of deleted keys, or zero when Redis is unavailable.
        """
        try:
            deleted = 0
            batch: list[bytes] = []
            for key in self._client.scan_iter(match=f"{prefix}*", count=100):
                batch.append(key)
                if len(batch) == 100:
                    deleted += int(self._client.delete(*batch))
                    batch.clear()
            if batch:
                deleted += int(self._client.delete(*batch))
            self._metrics.record_delete(stage_for_key(prefix), count=deleted)
            logger.info("Redis prefix cleared prefix=%s deleted=%d", prefix, deleted)
            return deleted
        except RedisError:
            self._metrics.record_error(stage_for_key(prefix))
            logger.exception(
                "CACHE ERROR stage=%s key_prefix=%s operation=clear_prefix",
                stage_for_key(prefix) or "unknown", key_prefix(prefix),
            )
            return 0

    def clear_project(self, project_id: str) -> int:
        """Invalidate every content-addressed pipeline artifact for a project."""
        resources = (
            "code-understanding", "code-provider", "code-enriched",
            "test-generation", "verification", "quality",
            "quality-checkpoint", "runtime-preparation",
        )
        return sum(
            self.clear_prefix(f"{resource}:{project_id}:")
            for resource in resources
        )


@lru_cache(maxsize=1)
def get_cache_manager() -> CacheManager:
    """Return the process-wide cache manager.

    Returns:
        A singleton CacheManager using the shared Redis connection pool.
    """
    return CacheManager(get_redis_client())
