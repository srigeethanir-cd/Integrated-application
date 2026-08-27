"""API response schemas for Redis cache observability."""

from pydantic import BaseModel, Field


class StageCacheStatistics(BaseModel):
    """Cache counters and calculated latency for one pipeline stage."""

    cache_hits: int
    cache_misses: int
    cache_hit_ratio: float
    cache_writes: int
    cache_deletes: int
    cache_errors: int
    cache_evictions: int
    average_read_latency_ms: float
    average_write_latency_ms: float


class RedisDiagnostics(BaseModel):
    """Sanitized Redis connection and optional server information."""

    connected: bool
    ping_latency_ms: float | None
    server_version: str | None
    memory_usage_bytes: int | None
    connected_clients: int | None
    expired_entries: int | None = None
    eviction_count: int | None = None
    error: str | None


class CacheStatisticsResponse(BaseModel):
    """Stage-specific cache metrics and aggregate Redis diagnostics."""

    stage3: StageCacheStatistics
    stage4: StageCacheStatistics
    stage5: StageCacheStatistics
    stage6: StageCacheStatistics
    runtime_preparation: StageCacheStatistics = Field(
        default_factory=lambda: StageCacheStatistics(
            cache_hits=0, cache_misses=0, cache_hit_ratio=0,
            cache_writes=0, cache_deletes=0, cache_errors=0,
            cache_evictions=0, average_read_latency_ms=0,
            average_write_latency_ms=0,
        )
    )
    overall_hit_ratio: float
    overall_miss_ratio: float = 0
    average_lookup_time_ms: float = 0
    cache_evictions: int
    redis: RedisDiagnostics
