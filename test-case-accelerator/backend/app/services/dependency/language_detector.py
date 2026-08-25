# backend/app/services/dependency/language_detector.py
"""Language Detector module.

Detects the programming language of a given file based on its extension
or simple heuristics. The actual detection logic will be added later.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

SupportedLanguage = Literal["python", "java", "javascript", "typescript", "unknown"]


class LanguageDetector:
    """Detect programming language for a file path.

    Methods return a ``SupportedLanguage`` literal. ``unknown`` is used when the
    language cannot be determined.
    """

    def detect(self, file_path: str | Path) -> SupportedLanguage:
        """Return the detected language for *file_path*.

        Args:
            file_path: Path to the source file.

        Returns:
            A ``SupportedLanguage`` value.
        """
        extension = Path(file_path).suffix.lower()
        return {
            ".py": "python",
            ".java": "java",
            ".js": "javascript",
            ".jsx": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
        }.get(extension, "unknown")
