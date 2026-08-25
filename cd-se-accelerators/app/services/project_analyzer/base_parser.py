"""
Abstract base class for framework-specific project parsers.

Every concrete parser implements ``parse()`` and returns a raw dict whose
shape matches the corresponding Pydantic ``*AnalysisResult`` model.  The
ABC intentionally knows nothing about *how* parsing is done (Node.js
subprocess, Python library, gRPC, etc.) — that is an implementation detail
of each subclass.

Adding a new framework requires:
1. Subclass ``BaseParser``.
2. Implement ``framework_name`` and ``parse()``.
3. Register the instance in ``ParserRegistry``.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict


class BaseParser(ABC):
    """Strategy interface that all project parsers must implement."""

    @property
    @abstractmethod
    def framework_name(self) -> str:
        """Human-readable name of the framework this parser targets."""
        ...

    @abstractmethod
    def parse(self, project_path: Path) -> Dict[str, Any]:
        """Parse the project at *project_path* and return structured data.

        Args:
            project_path: Absolute path to the project source directory.

        Returns:
            A dict matching the corresponding framework-specific Pydantic
            ``*AnalysisResult`` schema (e.g. ``ReactAnalysisResult``,
            ``AngularAnalysisResult``).

        Raises:
            RuntimeError: If the underlying parser fails (e.g. Node.js
                script exits with non-zero status).
            ValueError: If the project path is invalid.
        """
        ...
