"""Redis server diagnostics combined with application cache metrics."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from redis import Redis
from redis.exceptions import RedisError

from app.infrastructure.redis.client import get_redis_client
from app.infrastructure.redis.health import check_redis_health
from app.infrastructure.redis.metrics import (
    CacheMetricsRegistry,
    get_cache_metrics_registry,
)


class RedisDiagnosticsService:
    """Collect sanitized Redis health, capacity, client, and cache statistics."""

    def __init__(self, client: Redis, metrics: CacheMetricsRegistry) -> None:
        """Initialize diagnostics with shared infrastructure dependencies.

        Args:
            client: Singleton Redis client.
            metrics: Process-wide cache metrics registry.
        """
        self._client = client
        self._metrics = metrics

    def collect(self) -> dict[str, Any]:
        """Collect diagnostics without propagating Redis availability failures.

        Returns:
            Connectivity, latency, optional server data, and stage statistics.
        """
        health = check_redis_health(self._client)
        memory_usage_bytes = None
        connected_clients = None
        evicted_keys = None
        expired_keys = None
        if health.connected:
            memory_usage_bytes = self._info_value("memory", "used_memory")
            connected_clients = self._info_value("clients", "connected_clients")
            evicted_keys = self._info_value("stats", "evicted_keys")
            expired_keys = self._info_value("stats", "expired_keys")
            if isinstance(evicted_keys, int):
                self._metrics.set_overall_evictions(evicted_keys)
        statistics = self._metrics.snapshot()
        return {
            "redis": {
                "connected": health.connected,
                "ping_latency_ms": health.latency_ms,
                "server_version": health.server_version,
                "memory_usage_bytes": memory_usage_bytes,
                "connected_clients": connected_clients,
                "expired_entries": expired_keys,
                "eviction_count": evicted_keys,
                "error": health.error,
            },
            **statistics,
        }

    def _info_value(self, section: str, key: str) -> int | None:
        """Read one optional integer from a Redis INFO section.

        Args:
            section: Redis INFO section.
            key: Field name within that section.

        Returns:
            Integer value when supported, otherwise None.
        """
        try:
            value = self._client.info(section=section).get(key)
            return int(value) if value is not None else None
        except (RedisError, TypeError, ValueError):
            return None


@lru_cache(maxsize=1)
def get_redis_diagnostics_service() -> RedisDiagnosticsService:
    """Return diagnostics using the existing singleton client and metrics registry."""
    return RedisDiagnosticsService(
        get_redis_client(), get_cache_metrics_registry()
    )
