# backend/app/services/dependency/entrypoint_detector.py
"""Entrypoint Detector module.

Identifies potential entry‑point files for a given programming language.
Implementation will be added later.
"""

from __future__ import annotations

from pathlib import Path
from typing import List


class EntrypointDetector:
    """Detect entry‑point files within a collection of paths.

    The detection rules are language‑specific and will be defined in a later
    implementation.
    """

    def __init__(self) -> None:
        """Initialize the detector (no arguments required for now)."""
        pass

    def find_entrypoints(self, files: List[Path]) -> List[Path]:
        """Return a list of files that are considered entry points.

        Args:
            files: List of file paths to evaluate.

        Returns:
            List of paths that match known entry‑point patterns.
        """
        names = {
            "app.py", "main.py", "manage.py", "server.py", "index.js",
            "index.ts", "server.js", "server.ts", "Application.java",
        }
        return [path for path in files if path.name in names]
