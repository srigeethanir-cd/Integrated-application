"""
Redis Pipeline Cache Service – Intermediate State & Pipeline Persistence.

Provides low-latency, durable Redis caching for all 9 pipeline stages:
1. Source Ingestion
2. Project Scanner
3. Framework Detection
4. Project Analyzer (AST + Frontend Context + Behavior Inventory)
5. IR Generator
6. Strategy Engine
7. Edge Case Generator
8. Test Case Generator
9. Test Writer & Validation

Enables subsequent pipeline stages to retrieve outputs generated in previous stages
reliably across independent HTTP requests and container restarts.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

DEFAULT_REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/1")
PIPELINE_CACHE_TTL_SECONDS = int(os.getenv("PIPELINE_CACHE_TTL_SECONDS", "86400"))  # 24 hours


class RedisPipelineCacheManager:
    """Manages pipeline stage outputs and context persistence in Redis."""

    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url or os.getenv("REDIS_URL", DEFAULT_REDIS_URL)
        self._client = None
        self._connected = False
        self._fallback_memory_cache: Dict[str, Any] = {}
        self._init_connection()

    def _init_connection(self) -> None:
        """Attempt connection to Redis instance."""
        try:
            import redis
            self._client = redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_timeout=3.0,
                socket_connect_timeout=3.0,
            )
            self._client.ping()
            self._connected = True
            logger.info("RedisPipelineCacheManager: Successfully connected to Redis at %s", self.redis_url)
        except Exception as exc:
            self._connected = False
            self._client = None
            logger.warning(
                "RedisPipelineCacheManager: Could not connect to Redis (%s). Using fallback in-memory cache: %s",
                self.redis_url,
                exc,
            )

    @property
    def is_connected(self) -> bool:
        """Check if Redis connection is active."""
        if not self._connected or not self._client:
            return False
        try:
            self._client.ping()
            return True
        except Exception:
            self._connected = False
            return False

    def _serialize_data(self, data: Any) -> str:
        """Serialize arbitrary python / Pydantic data to JSON string."""
        if hasattr(data, "model_dump"):
            data = data.model_dump()
        elif hasattr(data, "dict") and callable(data.dict):
            data = data.dict()
        elif hasattr(data, "__dict__") and not isinstance(data, (dict, list, str, int, float, bool)):
            data = data.__dict__

        def _json_default(obj):
            if hasattr(obj, "model_dump"):
                return obj.model_dump()
            if hasattr(obj, "dict") and callable(obj.dict):
                return obj.dict()
            if hasattr(obj, "isoformat"):
                return obj.isoformat()
            if hasattr(obj, "__str__"):
                return str(obj)
            return None

        return json.dumps(data, default=_json_default)

    def save_stage_output(self, pipeline_run_id: str, stage_key: str, data: Any) -> bool:
        """Persist output of a pipeline stage to Redis under pipeline:{run_id}:stage:{stage_key}."""
        if not pipeline_run_id or not stage_key:
            return False

        key = f"pipeline:{pipeline_run_id}:stage:{stage_key}"
        try:
            serialized = self._serialize_data(data)
            if self.is_connected:
                self._client.set(key, serialized, ex=PIPELINE_CACHE_TTL_SECONDS)
                logger.info("Redis: Cached stage output for '%s' (key=%s, size=%d bytes)", stage_key, key, len(serialized))
            else:
                self._fallback_memory_cache[key] = json.loads(serialized)
            return True
        except Exception as exc:
            logger.warning("Redis: Failed to cache stage output for '%s': %s", stage_key, exc)
            return False

    def get_stage_output(self, pipeline_run_id: str, stage_key: str) -> Optional[Any]:
        """Retrieve cached output of a pipeline stage from Redis."""
        if not pipeline_run_id or not stage_key:
            return None

        key = f"pipeline:{pipeline_run_id}:stage:{stage_key}"
        try:
            if self.is_connected:
                raw = self._client.get(key)
                if raw:
                    logger.info("Redis: HIT stage cache for '%s' (key=%s)", stage_key, key)
                    return json.loads(raw)
            elif key in self._fallback_memory_cache:
                return self._fallback_memory_cache[key]
        except Exception as exc:
            logger.warning("Redis: Failed reading stage output for '%s': %s", stage_key, exc)

        return None

    def save_pipeline_context(self, pipeline_run_id: str, context_dict: Dict[str, Any]) -> bool:
        """Persist general pipeline context state (framework, paths, project IDs)."""
        if not pipeline_run_id:
            return False

        key = f"pipeline:{pipeline_run_id}:context"
        try:
            serialized = self._serialize_data(context_dict)
            if self.is_connected:
                self._client.set(key, serialized, ex=PIPELINE_CACHE_TTL_SECONDS)
            else:
                self._fallback_memory_cache[key] = json.loads(serialized)
            return True
        except Exception as exc:
            logger.warning("Redis: Failed to cache pipeline context for run '%s': %s", pipeline_run_id, exc)
            return False

    def get_pipeline_context(self, pipeline_run_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve general pipeline context state from Redis."""
        if not pipeline_run_id:
            return None

        key = f"pipeline:{pipeline_run_id}:context"
        try:
            if self.is_connected:
                raw = self._client.get(key)
                if raw:
                    return json.loads(raw)
            elif key in self._fallback_memory_cache:
                return self._fallback_memory_cache[key]
        except Exception as exc:
            logger.warning("Redis: Failed reading pipeline context for run '%s': %s", pipeline_run_id, exc)

        return None

    def list_cached_stages(self, pipeline_run_id: str) -> List[str]:
        """List all stage names currently cached in Redis for a specific pipeline run."""
        if not pipeline_run_id:
            return []

        stages = []
        pattern = f"pipeline:{pipeline_run_id}:stage:*"
        try:
            if self.is_connected:
                keys = self._client.keys(pattern)
                prefix = f"pipeline:{pipeline_run_id}:stage:"
                for k in keys:
                    if k.startswith(prefix):
                        stages.append(k[len(prefix):])
            else:
                prefix = f"pipeline:{pipeline_run_id}:stage:"
                for k in self._fallback_memory_cache:
                    if k.startswith(prefix):
                        stages.append(k[len(prefix):])
        except Exception as exc:
            logger.warning("Redis: Failed listing cached stages for run '%s': %s", pipeline_run_id, exc)

        return stages

    def clear_pipeline_run(self, pipeline_run_id: str) -> bool:
        """Delete all cached keys associated with a pipeline run."""
        if not pipeline_run_id:
            return False

        pattern = f"pipeline:{pipeline_run_id}:*"
        try:
            if self.is_connected:
                keys = self._client.keys(pattern)
                if keys:
                    self._client.delete(*keys)
                    logger.info("Redis: Cleared %d cached keys for run '%s'", len(keys), pipeline_run_id)
            else:
                to_delete = [k for k in self._fallback_memory_cache if k.startswith(f"pipeline:{pipeline_run_id}:")]
                for k in to_delete:
                    del self._fallback_memory_cache[k]
            return True
        except Exception as exc:
            logger.warning("Redis: Failed clearing pipeline run '%s': %s", pipeline_run_id, exc)
            return False
