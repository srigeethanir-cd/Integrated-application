"""
Base Validator – Module 9.

Defines the abstract interface that all concrete framework-specific validators
must implement.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from app.models.validation_models import ValidationReport


class BaseValidator(ABC):
    """Abstract base class for React and Angular validation engines."""

    @property
    @abstractmethod
    def framework(self) -> str:
        """Name of the framework supported by this validator (e.g. 'React')."""
        pass

    @abstractmethod
    def validate(
        self,
        test_files: List[str],
        manifest: Dict[str, Any],
        workspace_dir: str
    ) -> ValidationReport:
        """Execute E2E syntax validation, test runner checks, coverage mapping, and quality audits.

        Args:
            test_files: List of absolute file paths to the generated test suites.
            manifest: Parsed manifest file structure (test_manifest.json).
            workspace_dir: Parent output workspace folder.

        Returns:
            ValidationReport summary.
        """
        pass
