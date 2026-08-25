from unittest.mock import MagicMock

from redis.exceptions import ConnectionError

from app.infrastructure.redis.cache_manager import CacheManager
from app.infrastructure.redis.diagnostics import RedisDiagnosticsService
from app.infrastructure.redis.metrics import CacheMetricsRegistry


def test_cache_metrics_increment_and_calculate_stage_hit_ratio() -> None:
    registry = CacheMetricsRegistry()
    client = MagicMock()
    client.get.side_effect = [b'{"value": 1}', None]
    client.set.return_value = True
    client.delete.return_value = 1
    cache = CacheManager(client)
    cache._metrics = registry
    key = "code-understanding:project:hash"

    assert cache.get(key) == {"value": 1}
    assert cache.get(key) is None
    assert cache.set(key, {"value": 2}, ttl=60)
    assert cache.delete(key)

    stage = registry.snapshot()["stage3"]
    assert stage["cache_hits"] == 1
    assert stage["cache_misses"] == 1
    assert stage["cache_hit_ratio"] == 0.5
    assert stage["cache_writes"] == 1
    assert stage["cache_deletes"] == 1
    assert stage["average_read_latency_ms"] >= 0
    assert stage["average_write_latency_ms"] >= 0
    assert registry.snapshot()["overall_hit_ratio"] == 0.5


def test_cache_errors_are_attributed_to_the_correct_stage() -> None:
    registry = CacheMetricsRegistry()
    client = MagicMock()
    client.get.side_effect = ConnectionError("unavailable")
    cache = CacheManager(client)
    cache._metrics = registry

    assert cache.get("verification:project:run:hash") is None

    assert registry.snapshot()["stage5"]["cache_errors"] == 1


def test_diagnostics_collects_optional_server_information() -> None:
    registry = CacheMetricsRegistry()
    client = MagicMock()
    client.ping.return_value = True
    client.info.side_effect = lambda section: {
        "server": {"redis_version": "7.2"},
        "memory": {"used_memory": 1024},
        "clients": {"connected_clients": 3},
        "stats": {"evicted_keys": 4, "expired_keys": 9},
    }[section]

    result = RedisDiagnosticsService(client, registry).collect()

    assert result["redis"]["connected"] is True
    assert result["redis"]["memory_usage_bytes"] == 1024
    assert result["redis"]["connected_clients"] == 3
    assert result["cache_evictions"] == 4
    assert result["redis"]["expired_entries"] == 9
    assert result["redis"]["eviction_count"] == 4
    assert "overall_miss_ratio" in result
    assert "average_lookup_time_ms" in result
    assert "runtime_preparation" in result


def test_diagnostics_returns_fallback_when_redis_is_unavailable() -> None:
    client = MagicMock()
    client.ping.side_effect = ConnectionError("unavailable")

    result = RedisDiagnosticsService(client, CacheMetricsRegistry()).collect()

    assert result["redis"]["connected"] is False
    assert result["redis"]["error"] == "Redis unavailable (ConnectionError)"
    assert result["stage3"]["cache_hits"] == 0
