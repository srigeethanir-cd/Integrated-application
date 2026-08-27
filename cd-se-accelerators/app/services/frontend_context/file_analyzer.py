"""
File Analyzer & Context Cache Manager for FCE.

Manages file hashing, context caching by (project_id + source_file + file_hash),
and exclusion of ignored directories (node_modules, dist, build, coverage, .git).
"""

import hashlib
import logging
import os
from typing import Dict, Optional
from app.services.frontend_context.models import SingleComponentFrontendContext

logger = logging.getLogger(__name__)

# In-memory context cache: key = f"{project_id}:{source_file}:{file_hash}" -> List[SingleComponentFrontendContext]
_context_cache: Dict[str, SingleComponentFrontendContext] = {}


def compute_file_hash(file_path: str) -> str:
    """Compute SHA256 content hash for a file."""
    if not os.path.exists(file_path):
        return ""
    hasher = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                hasher.update(chunk)
        return hasher.hexdigest()[:16]
    except Exception:
        return ""


def get_cached_context(project_id: str, source_file: str, file_hash: str) -> Optional[SingleComponentFrontendContext]:
    """Retrieve cached frontend context for exact project_id, source_file, and file_hash."""
    key = f"{project_id}:{source_file}:{file_hash}"
    return _context_cache.get(key)


def set_cached_context(project_id: str, source_file: str, file_hash: str, context: SingleComponentFrontendContext) -> None:
    """Store extracted frontend context in cache."""
    key = f"{project_id}:{source_file}:{file_hash}"
    _context_cache[key] = context


def clear_context_cache() -> None:
    """Clear in-memory context cache."""
    _context_cache.clear()
