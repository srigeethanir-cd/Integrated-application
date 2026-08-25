"""Deterministic implementation identity for persisted pipeline artifacts."""

from __future__ import annotations

import hashlib
import json
from typing import Any


SEMANTIC_CONTRACT_VERSION = "semantic-contract-v1"
ARTIFACT_VERSION_KEY = "_artifact_version"


def fingerprint(value: Any) -> str:
    """Return a stable digest for JSON-compatible implementation metadata."""
    canonical = json.dumps(
        value, sort_keys=True, separators=(",", ":"), default=str
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def artifact_version_manifest(
    *,
    semantic: Any,
    generator: Any,
    verification: Any,
) -> dict[str, str]:
    """Build component digests plus a composite artifact identity."""
    components = {
        "semantic": fingerprint(semantic),
        "generator": fingerprint(generator),
        "verification": fingerprint(verification),
    }
    return {**components, "composite": fingerprint(components)}


__all__ = [
    "ARTIFACT_VERSION_KEY",
    "SEMANTIC_CONTRACT_VERSION",
    "artifact_version_manifest",
    "fingerprint",
]
