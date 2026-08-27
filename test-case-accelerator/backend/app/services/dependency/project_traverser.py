# backend/app/services/dependency/project_traverser.py
"""Project Traverser module.

Provides a class that recursively scans a given directory, respecting ignore
patterns, and yields file paths for further analysis.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, List

from .utils import is_source_file


class ProjectTraverser:
    """Utility that walks a project directory and returns file paths.

    The actual traversal logic will be implemented later.
    """

    def __init__(self, ignore_patterns: List[str] | None = None) -> None:
        """Initialize the traverser.

        Args:
            ignore_patterns: List of glob patterns to exclude from traversal.
        """
        self.ignore_patterns = ignore_patterns or []

    def scan(self, root_path: str | Path) -> Iterable[Path]:
        """Yield file paths under *root_path* respecting ignore patterns.

        Returns an iterator of :class:`pathlib.Path` objects.
        """
        root = Path(root_path).resolve()
        if not root.is_dir():
            raise FileNotFoundError(f"Project source directory not found: {root}")

        ignored_parts = {
            ".venv", "venv", "site-packages", "__pycache__", ".git",
            "node_modules", "dist", "build", ".pytest_cache", ".idea",
            ".vscode", "egg-info", "htmlcov", ".mypy_cache"
        }

        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue
            relative_path = path.relative_to(root)
            
            # Filter out files inside dependency/generated folders
            if any(part in ignored_parts for part in relative_path.parts):
                continue
                
            if any(relative_path.match(pattern) for pattern in self.ignore_patterns):
                continue
                
            if is_source_file(path):
                yield path
