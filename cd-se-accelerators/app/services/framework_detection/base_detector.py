"""
Abstract base class for individual framework detectors.

Every concrete detector implements ``detect()`` and returns a result dict
with ``framework``, ``confidence``, and ``reason`` keys.  New frameworks
are added by subclassing ``BaseFrameworkDetector`` and registering the
subclass in :pymod:`app.services.framework_detection.framework_detector_service`.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional


class BaseFrameworkDetector(ABC):
    """Contract that every framework-specific detector must fulfil."""

    @property
    @abstractmethod
    def framework_name(self) -> str:
        """Human-readable name of the framework this detector targets."""
        ...

    @abstractmethod
    def detect(
        self, project_path: Path, package_json: Optional[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Attempt to detect the framework in *project_path*.

        Args:
            project_path: Root directory of the project source.
            package_json: Parsed ``package.json`` contents, or ``None`` if
                the file does not exist.

        Returns:
            A dict ``{"framework": str, "confidence": int, "reason": str}``
            if the framework is detected, otherwise ``None``.
        """
        ...
