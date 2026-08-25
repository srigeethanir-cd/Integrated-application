from unittest.mock import MagicMock

from app.infrastructure.redis.diagnostics import get_redis_diagnostics_service
from app.main import app


def test_cache_statistics_endpoint_returns_stage_metrics_and_diagnostics(client) -> None:
    diagnostics = MagicMock()
    empty_stage = {
        "cache_hits": 0,
        "cache_misses": 0,
        "cache_hit_ratio": 0.0,
        "cache_writes": 0,
        "cache_deletes": 0,
        "cache_errors": 0,
        "cache_evictions": 0,
        "average_read_latency_ms": 0.0,
        "average_write_latency_ms": 0.0,
    }
    diagnostics.collect.return_value = {
        "stage3": {**empty_stage, "cache_hits": 3, "cache_misses": 1,
                   "cache_hit_ratio": 0.75},
        "stage4": empty_stage,
        "stage5": empty_stage,
        "stage6": empty_stage,
        "overall_hit_ratio": 0.75,
        "cache_evictions": 0,
        "redis": {
            "connected": True,
            "ping_latency_ms": 4.2,
            "server_version": "7.2",
            "memory_usage_bytes": 2048,
            "connected_clients": 2,
            "error": None,
        },
    }
    app.dependency_overrides[get_redis_diagnostics_service] = lambda: diagnostics

    response = client.get("/cache/statistics")

    assert response.status_code == 200
    assert response.json()["stage3"]["cache_hit_ratio"] == 0.75
    assert response.json()["redis"]["connected"] is True
