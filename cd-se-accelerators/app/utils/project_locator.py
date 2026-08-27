"""
Project Locator utility.

Recursively scans extracted archive directories to detect the actual
frontend project root based on key indicator files and structures.
"""

import logging
from pathlib import Path
from typing import List, Tuple

logger = logging.getLogger(__name__)

# Indicator file names and their relative scores
PRIMARY_INDICATORS = {
    "package.json": 10,
    "angular.json": 8,
    "next.config.js": 8,
    "next.config.ts": 8,
    "vite.config.js": 8,
    "vite.config.ts": 8,
    "tsconfig.json": 5,
}

_IGNORED_DIR_NAMES = {
    "node_modules",
    ".git",
    "__pycache__",
    ".next",
    ".cache",
    ".turbo",
    "dist",
    "build",
    "coverage",
}


def locate_project_root(search_dir: Path) -> Path:
    """Locate the root directory of a frontend project inside *search_dir*.

    Args:
        search_dir: Root directory to begin searching from.

    Returns:
        Path pointing to the detected project root directory.

    Raises:
        ValueError: If directory is empty, or no valid project root can be located.
    """
    search_dir = search_dir.resolve()
    if not search_dir.exists():
        raise FileNotFoundError(f"Search directory does not exist: {search_dir}")
    if not search_dir.is_dir():
        raise ValueError(f"Search directory is not a directory: {search_dir}")

    # Check if search directory is empty
    dir_items = [p for p in search_dir.iterdir() if p.name not in _IGNORED_DIR_NAMES]
    if not dir_items:
        raise ValueError("Project directory is empty.")

    candidates: List[Tuple[int, int, Path]] = []

    def _depth(p: Path) -> int:
        return len(p.relative_to(search_dir).parts)

    for current_root, dirs, files in search_dir.walk():
        # Remove ignored directories in-place so walk doesn't descend into them
        dirs[:] = [d for d in dirs if d not in _IGNORED_DIR_NAMES]

        current_path = Path(current_root)
        score = 0

        # Check file indicators
        for filename in files:
            if filename in PRIMARY_INDICATORS:
                score += PRIMARY_INDICATORS[filename]

        # Check directory indicators (e.g., src/)
        if "src" in dirs and (current_path / "src").is_dir():
            score += 3

        if score > 0:
            depth = _depth(current_path)
            # Tuple order: (score descending, depth ascending)
            candidates.append((score, depth, current_path))

    if candidates:
        # Sort candidates: highest score first, then shallowest depth
        candidates.sort(key=lambda item: (-item[0], item[1]))
        best_match = candidates[0][2]
        logger.info(
            "Project root detected at %s (score=%d, depth=%d)",
            best_match,
            candidates[0][0],
            candidates[0][1],
        )
        return best_match

    # If no indicators matched, check if search_dir has a single top-level folder
    if len(dir_items) == 1 and dir_items[0].is_dir():
        single_subfolder = dir_items[0]
        # Check if single subfolder has any files
        sub_items = [p for p in single_subfolder.iterdir() if p.name not in _IGNORED_DIR_NAMES]
        if sub_items:
            logger.info("Defaulting to single top-level folder as project root: %s", single_subfolder)
            return single_subfolder

    # Check if there are non-empty files directly in search_dir as fallback
    files_in_root = [p for p in dir_items if p.is_file()]
    if files_in_root:
        # No recognized frontend indicators found
        raise ValueError("No frontend project detected inside ZIP.")

    raise ValueError("Unable to locate project root.")
