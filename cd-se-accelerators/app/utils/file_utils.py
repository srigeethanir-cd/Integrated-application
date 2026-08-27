"""
Utility helpers for file system operations.
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def ensure_directory(path: Path) -> Path:
    """Create directory (and parents) if it does not already exist.

    Args:
        path: The directory path to ensure exists.

    Returns:
        The same path, for chaining convenience.
    """
    path.mkdir(parents=True, exist_ok=True)
    logger.debug("Ensured directory exists: %s", path)
    return path


def validate_directory_exists(path: Path) -> None:
    """Raise ValueError if *path* is not an existing directory.

    Args:
        path: The path to validate.

    Raises:
        ValueError: If the path does not exist or is not a directory.
    """
    if not path.exists():
        raise ValueError(f"Path does not exist: {path}")
    if not path.is_dir():
        raise ValueError(f"Path is not a directory: {path}")


def validate_zip_extension(filename: str) -> None:
    """Raise ValueError if *filename* does not have a .zip extension.

    Args:
        filename: The filename to validate.

    Raises:
        ValueError: If the filename does not end with .zip.
    """
    if not filename.lower().endswith(".zip"):
        raise ValueError(
            f"Invalid file extension. Expected .zip, got: {filename}"
        )
