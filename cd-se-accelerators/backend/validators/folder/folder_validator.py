"""Folder Validator verifying folder structure and layout."""

import logging
from pathlib import Path
from typing import Any, Dict
from validators.models import ValidationResult, ValidationSeverity

logger = logging.getLogger(__name__)


class FolderValidator:
    """Validates project directory structure and required layout paths."""

    REQUIRED_PATHS = ["backend", "frontend", "docs"]

    def validate(self, project_root: str) -> ValidationResult:
        """Validate project folder layout."""
        root = Path(project_root)
        missing = [p for p in self.REQUIRED_PATHS if not (root / p).exists()]

        if not root.exists():
            return ValidationResult(
                validator_name="FolderValidator",
                passed=False,
                severity=ValidationSeverity.CRITICAL,
                recommended_fixes=["Create target project directory and scaffold root folders"],
                retry_eligible=True,
                details=f"Project root directory '{project_root}' does not exist.",
            )

        if missing:
            return ValidationResult(
                validator_name="FolderValidator",
                passed=False,
                severity=ValidationSeverity.HIGH,
                recommended_fixes=[f"Scaffold missing directories: {', '.join(missing)}"],
                retry_eligible=True,
                details=f"Missing required project directories: {', '.join(missing)}.",
            )

        return ValidationResult(
            validator_name="FolderValidator",
            passed=True,
            severity=ValidationSeverity.LOW,
            recommended_fixes=[],
            retry_eligible=True,
            details="Folder structure and layout verified successfully.",
        )
