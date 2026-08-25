"""Thread-safe in-process Redis cache metrics."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from threading import Lock

STAGES = ("stage3", "stage4", "stage5", "stage6", "runtime_preparation")
PREFIX_STAGE = {
    "code-understanding": "stage3",
    "test-generation": "stage4",
    "verification": "stage5",
    "quality": "stage6",
    "quality-checkpoint": "stage6",
    "code-provider": "stage3",
    "code-enriched": "stage3",
    "runtime-preparation": "runtime_preparation",
}


@dataclass(slots=True)
class _StageCounters:
    """Mutable counters protected by CacheMetricsRegistry's lock."""

    cache_hits: int = 0
    cache_misses: int = 0
    cache_writes: int = 0
    cache_deletes: int = 0
    cache_errors: int = 0
    cache_evictions: int = 0
    read_latency_total_ms: float = 0.0
    read_operations: int = 0
    write_latency_total_ms: float = 0.0
    write_operations: int = 0


class CacheMetricsRegistry:
    """Collect cache metrics independently for pipeline Stages 3 through 6."""

    def __init__(self) -> None:
        """Initialize zeroed stage counters and a synchronization lock."""
        self._lock = Lock()
        self._stages = {stage: _StageCounters() for stage in STAGES}
        self._server_evictions = 0

    def record_read(self, stage: str | None, *, hit: bool, latency_ms: float) -> None:
        """Record a cache lookup.

        Args:
            stage: Stage name inferred from the key, or None when unrelated.
            hit: Whether the requested value existed.
            latency_ms: Complete Redis read latency in milliseconds.
        """
        counters = self._counter(stage)
        if counters is None:
            return
        with self._lock:
            if hit:
                counters.cache_hits += 1
            else:
                counters.cache_misses += 1
            counters.read_latency_total_ms += latency_ms
            counters.read_operations += 1

    def record_write(self, stage: str | None, *, latency_ms: float) -> None:
        """Record a successful cache write and its latency."""
        counters = self._counter(stage)
        if counters is None:
            return
        with self._lock:
            counters.cache_writes += 1
            counters.write_latency_total_ms += latency_ms
            counters.write_operations += 1

    def record_delete(self, stage: str | None, *, count: int = 1) -> None:
        """Record deleted keys for a stage."""
        counters = self._counter(stage)
        if counters is None:
            return
        with self._lock:
            counters.cache_deletes += max(0, count)

    def record_error(self, stage: str | None) -> None:
        """Record a failed cache operation for a stage."""
        counters = self._counter(stage)
        if counters is None:
            return
        with self._lock:
            counters.cache_errors += 1

    def set_overall_evictions(self, count: int) -> None:
        """Record Redis server evictions when per-stage attribution is unavailable."""
        with self._lock:
            for counters in self._stages.values():
                counters.cache_evictions = 0
            # Redis exposes only a server-wide count, so it cannot be attributed.
            self._server_evictions = max(0, count)

    def snapshot(self) -> dict[str, object]:
        """Return immutable calculated metrics and aggregate hit ratio."""
        with self._lock:
            stages = {
                stage: self._snapshot_counter(counters)
                for stage, counters in self._stages.items()
            }
            total_hits = sum(item.cache_hits for item in self._stages.values())
            total_misses = sum(item.cache_misses for item in self._stages.values())
            requests = total_hits + total_misses
            return {
                **stages,
                "overall_hit_ratio": round(total_hits / requests, 4) if requests else 0.0,
                "overall_miss_ratio": round(total_misses / requests, 4) if requests else 0.0,
                "average_lookup_time_ms": round(
                    sum(item.read_latency_total_ms for item in self._stages.values())
                    / sum(item.read_operations for item in self._stages.values()),
                    3,
                ) if sum(item.read_operations for item in self._stages.values()) else 0.0,
                "cache_evictions": self._server_evictions,
            }

    def reset(self) -> None:
        """Reset all counters; intended for deterministic tests."""
        with self._lock:
            self._stages = {stage: _StageCounters() for stage in STAGES}
            self._server_evictions = 0

    def _counter(self, stage: str | None) -> _StageCounters | None:
        """Return mutable counters for a recognized stage."""
        return self._stages.get(stage) if stage else None

    @staticmethod
    def _snapshot_counter(counters: _StageCounters) -> dict[str, int | float]:
        """Calculate ratios and averages for one stage."""
        reads = counters.cache_hits + counters.cache_misses
        return {
            "cache_hits": counters.cache_hits,
            "cache_misses": counters.cache_misses,
            "cache_hit_ratio": round(counters.cache_hits / reads, 4) if reads else 0.0,
            "cache_writes": counters.cache_writes,
            "cache_deletes": counters.cache_deletes,
            "cache_errors": counters.cache_errors,
            "cache_evictions": counters.cache_evictions,
            "average_read_latency_ms": round(
                counters.read_latency_total_ms / counters.read_operations, 3
            ) if counters.read_operations else 0.0,
            "average_write_latency_ms": round(
                counters.write_latency_total_ms / counters.write_operations, 3
            ) if counters.write_operations else 0.0,
        }


def stage_for_key(key: str) -> str | None:
    """Infer a pipeline stage from a standardized cache key.

    Args:
        key: Cache key or prefix.

    Returns:
        Stage name when recognized, otherwise None.
    """
    normalized = key.removeprefix("testforge:")
    return PREFIX_STAGE.get(normalized.split(":", 1)[0])


def key_prefix(key: str) -> str:
    """Return the non-sensitive resource prefix of a cache key."""
    normalized = key.removeprefix("testforge:")
    return normalized.split(":", 1)[0]


@lru_cache(maxsize=1)
def get_cache_metrics_registry() -> CacheMetricsRegistry:
    """Return the process-wide cache metrics registry."""
    return CacheMetricsRegistry()
