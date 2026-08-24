"""Validation Framework orchestrating all 10 independent modular validators."""

import logging
from typing import Any, Dict, List

from validators.api.api_validator import APIValidator
from validators.database_validator import DatabaseValidator
from validators.dependency.dependency_validator import DependencyValidator
from validators.folder.folder_validator import FolderValidator
from validators.models import OverallValidationReport, ValidationResult, ValidationSeverity
from validators.performance_validator import PerformanceValidator
from validators.quality.quality_validator import QualityValidator
from validators.runtime.runtime_validator import RuntimeValidator
from validators.security.security_validator import SecurityValidator
from validators.traceability.traceability_validator import TraceabilityValidator

logger = logging.getLogger(__name__)


class ValidationFramework:
    """Orchestrates execution across all 10 independent modular validators."""

    def __init__(self):
        self.folder_validator = FolderValidator()
        self.api_validator = APIValidator()
        self.dependency_validator = DependencyValidator()
        self.runtime_validator = RuntimeValidator()
        self.database_validator = DatabaseValidator()
        self.security_validator = SecurityValidator()
        self.quality_validator = QualityValidator()
        self.performance_validator = PerformanceValidator()
        self.traceability_validator = TraceabilityValidator()

    def run_all_validators(
        self,
        project_root: str,
        master_blueprint: Dict[str, Any] = None,
        dag: Dict[str, Any] = None,
    ) -> OverallValidationReport:
        """Run all 10 independent validators and compile overall diagnostic report."""
        logger.info("ValidationFramework: Running all 10 modular validators on %s", project_root)
        results: List[ValidationResult] = []

        # Run 10 validators
        results.append(self.folder_validator.validate(project_root))
        results.append(self.api_validator.validate(project_root, master_blueprint=master_blueprint))
        results.append(self.dependency_validator.validate(project_root, dag=dag))
        results.append(self.runtime_validator.validate(project_root))
        results.append(self.database_validator.validate(project_root))
        results.append(self.security_validator.validate(project_root))
        results.append(self.quality_validator.validate(project_root))
        results.append(self.performance_validator.validate(project_root))
        results.append(self.traceability_validator.validate(project_root))

        passed_count = sum(1 for r in results if r.passed)
        failed_count = len(results) - passed_count
        overall_passed = failed_count == 0

        logger.info(
            "ValidationFramework: Completed. Passed %d/%d validators.",
            passed_count,
            len(results),
        )

        return OverallValidationReport(
            project_name=project_root.split("/")[-1] if "/" in project_root else project_root,
            total_validators=len(results),
            passed_count=passed_count,
            failed_count=failed_count,
            overall_passed=overall_passed,
            results=results,
        )
