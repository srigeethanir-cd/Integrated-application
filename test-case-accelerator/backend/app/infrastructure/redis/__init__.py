"""Public Redis infrastructure API for future application integrations."""

from app.infrastructure.redis.cache_manager import CacheManager, get_cache_manager
from app.infrastructure.redis.client import close_redis_client, get_redis_client
from app.infrastructure.redis.health import RedisHealth, check_redis_health
from app.infrastructure.redis.key_builder import CacheKeyBuilder
from app.infrastructure.redis.ttl import CacheTTL
from app.infrastructure.redis.diagnostics import (
    RedisDiagnosticsService,
    get_redis_diagnostics_service,
)
from app.infrastructure.redis.metrics import (
    CacheMetricsRegistry,
    get_cache_metrics_registry,
)

__all__ = [
    "CacheKeyBuilder",
    "CacheManager",
    "CacheTTL",
    "RedisHealth",
    "RedisDiagnosticsService",
    "CacheMetricsRegistry",
    "check_redis_health",
    "close_redis_client",
    "get_cache_manager",
    "get_redis_client",
    "get_redis_diagnostics_service",
    "get_cache_metrics_registry",
]
