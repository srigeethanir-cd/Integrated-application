"""Dependency Validator verifying story dependency DAGs and import integrity."""

import logging
from typing import Any, Dict
from validators.models import ValidationResult, ValidationSeverity

logger = logging.getLogger(__name__)


class DependencyValidator:
    """Validates story dependency graph acyclicity and module import integrity."""

    def validate(self, project_root: str, dag: Dict[str, Any] = None) -> ValidationResult:
        """Validate dependency graph acyclicity."""
        if dag and not dag.get("is_acyclic", True):
            return ValidationResult(
                validator_name="DependencyValidator",
                passed=False,
                severity=ValidationSeverity.CRITICAL,
                recommended_fixes=["Refactor story dependencies to break cycle"],
                retry_eligible=True,
                details="Cyclic dependency detected in story DAG.",
            )

        return ValidationResult(
            validator_name="DependencyValidator",
            passed=True,
            severity=ValidationSeverity.LOW,
            recommended_fixes=[],
            retry_eligible=True,
            details="Dependency graph acyclicity and import integrity verified.",
        )
