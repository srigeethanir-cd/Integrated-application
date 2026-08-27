"""Public serialization boundary for persisted pipeline artifacts."""

from __future__ import annotations

from typing import Any

_INTERNAL_PIPELINE_FIELDS = frozenset({
    "_artifact_version",
    "quality_checkpoint",
})


def public_pipeline_result(payload: Any) -> Any:
    """Return a transport-safe copy without mutating persisted state."""
    if not isinstance(payload, dict):
        return payload
    return {
        key: value
        for key, value in payload.items()
        if key not in _INTERNAL_PIPELINE_FIELDS
    }


__all__ = ["public_pipeline_result"]
