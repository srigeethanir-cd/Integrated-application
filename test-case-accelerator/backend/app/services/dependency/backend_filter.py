# backend/app/services/dependency/backend_filter.py
"""Backend Filter module.

Filters a collection of file paths to retain only those that belong to the
backend portion of the project (e.g., ``.py`` files under ``backend/app``).
Actual filtering criteria will be defined later.
"""

from __future__ import annotations

from pathlib import Path
from typing import List


class BackendFilter:
    """Utility class that filters backend source files.

    The filter logic will be implemented in a future commit.
    """

    def __init__(self, backend_root: str | Path | None = None) -> None:
        """Initialize with the absolute path to the backend root directory.

        Args:
            backend_root: Path to the backend source root (e.g., ``backend/app``).
        """
        self.backend_root = Path(backend_root).resolve() if backend_root else None

    def filter(self, files: List[Path]) -> List[Path]:
        """Return only the files that are considered part of the backend.

        Args:
            files: List of file paths to evaluate.

        Returns:
            Subset of *files* that match backend criteria.
        """
        if self.backend_root is None:
            return files
        return [path for path in files if path.resolve().is_relative_to(self.backend_root)]
