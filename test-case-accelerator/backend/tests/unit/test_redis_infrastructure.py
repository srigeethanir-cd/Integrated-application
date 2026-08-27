from datetime import UTC, datetime
from unittest.mock import MagicMock
from uuid import UUID

from redis.exceptions import ConnectionError

from app.infrastructure.redis.cache_manager import CacheManager
from app.infrastructure.redis.health import check_redis_health
from app.infrastructure.redis.key_builder import CacheKeyBuilder
from app.infrastructure.redis.serializers import JsonSerializer


def test_json_serializer_round_trip_supports_structured_values() -> None:
    value = {
        "project_id": UUID("12345678-1234-5678-1234-567812345678"),
        "created_at": datetime(2026, 7, 22, tzinfo=UTC),
        "results": [1, True, None],
    }

    decoded = JsonSerializer.loads(JsonSerializer.dumps(value))

    assert decoded == {
        "project_id": "12345678-1234-5678-1234-567812345678",
        "created_at": "2026-07-22T00:00:00+00:00",
        "results": [1, True, None],
    }


def test_cache_manager_serializes_and_deserializes_json() -> None:
    client = MagicMock()
    client.set.return_value = True
    client.get.return_value = b'{"status": "ready"}'
    cache = CacheManager(client)

    assert cache.set("testforge:project:1", {"status": "ready"}, ttl=60)
    assert cache.get("testforge:project:1") == {"status": "ready"}
    client.set.assert_called_once_with(
        "testforge:project:1", b'{"status": "ready"}', ex=60
    )


def test_cache_manager_falls_back_when_redis_is_unavailable() -> None:
    client = MagicMock()
    client.get.side_effect = ConnectionError("unavailable")
    cache = CacheManager(client)

    assert cache.get("testforge:project:1") is None


def test_project_invalidation_scans_pipeline_artifact_prefixes() -> None:
    client = MagicMock()
    client.scan_iter.return_value = []
    cache = CacheManager(client)

    assert cache.clear_project("project-1") == 0

    patterns = [item.kwargs["match"] for item in client.scan_iter.call_args_list]
    assert "code-provider:project-1:*" in patterns
    assert "code-enriched:project-1:*" in patterns
    assert "runtime-preparation:project-1:*" in patterns
    assert "quality-checkpoint:project-1:*" in patterns


def test_key_builder_standardizes_pipeline_keys() -> None:
    assert CacheKeyBuilder.project("p1") == "testforge:project:p1"
    assert CacheKeyBuilder.code_understanding("r1") == "testforge:code-understanding:r1"
    assert CacheKeyBuilder.runtime("r2") == "testforge:runtime:r2"


def test_health_check_returns_sanitized_server_details() -> None:
    client = MagicMock()
    client.ping.return_value = True
    client.info.return_value = {"redis_version": "7.2.0"}

    health = check_redis_health(client)

    assert health.connected is True
    assert health.latency_ms is not None
    assert health.server_version == "7.2.0"
    assert health.error is None
