"""
Temporary Workspace Management utility.

Creates isolated, uniquely named temporary workspace directories under
``temp/uploads/<uuid>/`` and provides context manager based cleanup.
"""

import logging
import shutil
import uuid
from pathlib import Path
from typing import Generator

logger = logging.getLogger(__name__)

# Base root directory for temporary extracted workspaces
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_TEMP_ROOT = _PROJECT_ROOT / "temp" / "uploads"


class TempWorkspace:
    """Context manager for temporary workspace lifecycle management."""

    def __init__(self, temp_root: Path | None = None) -> None:
        self._temp_root = temp_root or _DEFAULT_TEMP_ROOT
        self._temp_dir: Path | None = None

    @property
    def workspace_path(self) -> Path:
        """Return the active temporary workspace path."""
        if self._temp_dir is None:
            raise RuntimeError("TempWorkspace is not active. Use within a 'with' context.")
        return self._temp_dir

    def __enter__(self) -> Path:
        self._temp_root.mkdir(parents=True, exist_ok=True)
        unique_id = uuid.uuid4().hex
        self._temp_dir = self._temp_root / unique_id
        self._temp_dir.mkdir(parents=True, exist_ok=False)
        logger.info("Created temporary workspace: %s", self._temp_dir)
        return self._temp_dir

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._temp_dir and self._temp_dir.exists():
            try:
                shutil.rmtree(self._temp_dir, ignore_errors=True)
                logger.info(
                    "Cleanup status: Temporary workspace %s cleaned up successfully",
                    self._temp_dir,
                )
            except Exception as exc:
                logger.warning(
                    "Cleanup status: Failed to delete temporary workspace %s: %s",
                    self._temp_dir,
                    exc,
                )
        self._temp_dir = None
