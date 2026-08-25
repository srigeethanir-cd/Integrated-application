# backend/app/services/dependency/utils.py
"""Utility helpers for the dependency discovery package.

This module will house small helper functions that are used across the
dependency sub‑modules. Currently only placeholders are provided.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, List


def is_source_file(file_path: str | Path) -> bool:
    """Return ``True`` if *file_path* looks like a source file.

    The concrete implementation (extension checks, etc.) will be added
    later.
    """
    return Path(file_path).suffix.lower() in {
        ".py", ".java", ".js", ".jsx", ".ts", ".tsx"
    }


def normalize_path(file_path: str | Path) -> Path:
    """Return a normalized absolute :class:`pathlib.Path`.

    Placeholder for future path‑normalisation logic.
    """
    return Path(file_path).expanduser().resolve()


def chunk_iterable(iterable: Iterable, size: int) -> List[Iterable]:
    """Split *iterable* into chunks of *size* elements.

    Used for batch DB inserts. Implementation pending.
    """
    if size <= 0:
        raise ValueError("Chunk size must be positive")
    items = list(iterable)
    return [items[index : index + size] for index in range(0, len(items), size)]
