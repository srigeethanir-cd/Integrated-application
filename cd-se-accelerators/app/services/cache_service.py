"""
Analysis Cache Service – SHA-256 Content Hashing & Storage.

Manages caching for expensive component analysis operations.
Unchanged files (matching SHA-256 content hash) bypass redundant parser and LLM analysis.
"""

import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class AnalysisCacheManager:
    """Manages file-level analysis caching with persistent disk storage."""

    def __init__(self, persistent_cache_dir: Optional[str] = None) -> None:
        self._memory_cache: Dict[str, Dict[str, Any]] = {}
        self._hits = 0
        self._misses = 0
        self._persistent_cache_dir = persistent_cache_dir or "temp/analysis_cache"
        os.makedirs(self._persistent_cache_dir, exist_ok=True)

    @staticmethod
    def build_cache_key(file_path: str, file_hash: str, framework: str, project_id: Optional[str] = None) -> str:
        """Construct a unique SHA-256 cache key including project_id for cross-project isolation."""
        pid = project_id or "default_project"
        raw = f"{pid}:{file_path}:{file_hash}:{framework.lower()}".encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    def get(self, file_path: str, file_hash: str, framework: str, project_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Retrieve cached component analysis if valid for this specific project_id.

        Args:
            file_path: Relative path of the file.
            file_hash: SHA-256 hash of file content.
            framework: Framework name.
            project_id: Unique project identifier.

        Returns:
            Cached dictionary or None on cache miss.
        """
        if not file_hash:
            self._misses += 1
            return None

        cache_key = self.build_cache_key(file_path, file_hash, framework, project_id=project_id)

        # 1. Check in-memory cache
        if cache_key in self._memory_cache:
            self._hits += 1
            logger.debug("Cache HIT (memory) for file '%s' (key=%s)", file_path, cache_key[:8])
            return self._memory_cache[cache_key]

        # 2. Check persistent disk cache
        disk_file = os.path.join(self._persistent_cache_dir, f"{cache_key}.json")
        if os.path.exists(disk_file):
            try:
                with open(disk_file, "r", encoding="utf-8") as f:
                    cached_data = json.load(f)
                self._memory_cache[cache_key] = cached_data
                self._hits += 1
                logger.debug("Cache HIT (disk) for file '%s' (key=%s)", file_path, cache_key[:8])
                return cached_data
            except Exception as exc:
                logger.warning("Failed reading disk cache for key %s: %s", cache_key, exc)

        self._misses += 1
        logger.debug("Cache MISS for file '%s' (key=%s)", file_path, cache_key[:8])
        return None

    def set(self, file_path: str, file_hash: str, framework: str, data: Dict[str, Any], project_id: Optional[str] = None) -> None:
        """Store component analysis in memory and disk cache.

        Args:
            file_path: Relative path of the file.
            file_hash: SHA-256 hash of file content.
            framework: Framework name.
            data: Analysis result payload to cache.
            project_id: Unique project identifier.
        """
        if not file_hash or not data:
            return

        cache_key = self.build_cache_key(file_path, file_hash, framework, project_id=project_id)
        self._memory_cache[cache_key] = data

        disk_file = os.path.join(self._persistent_cache_dir, f"{cache_key}.json")
        try:
            with open(disk_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            logger.debug("Cached analysis stored for file '%s' (key=%s)", file_path, cache_key[:8])
        except Exception as exc:
            logger.warning("Failed writing disk cache for key %s: %s", cache_key, exc)

    def get_stats(self) -> Tuple[int, int, float]:
        """Return tuple of (hits, misses, hit_rate_percentage)."""
        total = self._hits + self._misses
        hit_rate = round((self._hits / total * 100.0), 2) if total > 0 else 0.0
        return self._hits, self._misses, hit_rate

    def reset_stats(self) -> None:
        """Reset hit/miss performance counters."""
        self._hits = 0
        self._misses = 0

    def save_run_cache(self, run_dir: str) -> None:
        """Persist current run's active cache entries to run directory."""
        try:
            run_cache_file = os.path.join(run_dir, "cache_summary.json")
            hits, misses, hit_rate = self.get_stats()
            summary = {
                "hits": hits,
                "misses": misses,
                "hit_rate_percent": hit_rate,
                "cached_entries": len(self._memory_cache)
            }
            with open(run_cache_file, "w", encoding="utf-8") as f:
                json.dump(summary, f, indent=2)
        except Exception as exc:
            logger.warning("Failed persisting run cache summary: %s", exc)
