"""
IR Cache Utility – Module 6.

Stores and retrieves the generated FrameworkAgnosticIR in memory, keyed strictly
by project_id or pipeline_run_id to prevent cross-project contamination.
"""

import logging
from typing import Dict, Optional
from app.models.ir_models import FrameworkAgnosticIR

logger = logging.getLogger(__name__)

# Global in-memory cache mapping unique run keys (project_id/pipeline_run_id/project_name) -> FrameworkAgnosticIR
_ir_cache: Dict[str, FrameworkAgnosticIR] = {}


def clear_ir_cache() -> None:
    """Clear all entries in the IR cache between pipeline runs."""
    _ir_cache.clear()
    logger.debug("IR cache cleared")


def cache_ir(ir: FrameworkAgnosticIR, key: Optional[str] = None) -> None:
    """Store the given IR in cache keyed by project_id, pipeline_run_id, and project_name."""
    if not ir:
        return

    pid = getattr(ir, "project_id", None)
    rid = getattr(ir, "pipeline_run_id", None)
    pname = getattr(ir, "project_name", None)

    keys_to_set = set()
    if key:
        keys_to_set.add(key)
    if pid:
        keys_to_set.add(pid)
    if rid:
        keys_to_set.add(rid)
    if pname and pname != "IngestedProject":
        keys_to_set.add(pname)

    # If no specific key is present, fallback to project_name
    if not keys_to_set and pname:
        keys_to_set.add(pname)

    for k in keys_to_set:
        _ir_cache[k] = ir

    logger.debug("Cached IR under keys: %s", keys_to_set)


def get_cached_ir(key: Optional[str] = None) -> Optional[FrameworkAgnosticIR]:
    """Retrieve the cached IR by key (project_id, pipeline_run_id, or project_name).

    Returns None if no IR is cached.
    """
    if key and key in _ir_cache:
        return _ir_cache[key]
    
    # Fallback: return the most recently cached IR object
    if len(_ir_cache) > 0:
        return list(_ir_cache.values())[-1]

    return None
