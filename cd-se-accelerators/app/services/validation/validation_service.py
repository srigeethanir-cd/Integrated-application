"""
Validation Service – Module 9.

Orchestrates test manifest checks, test file AST auditing, E2E validation JSON exports,
and HTML/JSON coverage directory generation.
"""

import json
import logging
import os
from typing import Any, Dict, List, Union

from app.models.validation_models import CoverageStats, ValidationReport
from app.services.validation.react_validator import ReactValidator
from app.services.validation.angular_validator import AngularValidator
from app.services.validation.validation_registry import ValidationRegistry

logger = logging.getLogger(__name__)


def _build_default_registry() -> ValidationRegistry:
    registry = ValidationRegistry()
    registry.register(ReactValidator())
    registry.register(AngularValidator())
    return registry


class ValidationService:
    """Orchestrates E2E compiler parsing, Quality Auditing, and Coverage exports."""

    def __init__(self, registry: ValidationRegistry | None = None) -> None:
        self._registry = registry or _build_default_registry()
        logger.info(
            "ValidationService initialised with registry: %s",
            ", ".join(v.framework for v in self._registry._validators.values())
        )

    def run_validation(self, project_path: str, framework: str) -> ValidationReport:
        logger.info("ValidationService: Starting validation run for path: %s", project_path)

        # 1. Look for test_manifest.json
        manifest_path = os.path.join(project_path, "test_manifest.json")
        if not os.path.exists(manifest_path):
            raise FileNotFoundError(f"Missing test_manifest.json inside project path: '{project_path}'")

        # Read manifest
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        manifest_framework = manifest.get("framework", "")
        if manifest_framework.lower() != framework.lower():
            raise ValueError(
                f"Framework mismatch: Request specified '{framework}' but manifest indicates '{manifest_framework}'."
            )

        # 2. Gather files from manifest
        generated_files_info = manifest.get("generated_files", [])
        sub_folder = "react" if framework.lower() == "react" else "angular"
        tests_dir = os.path.join(project_path, "tests", sub_folder)

        test_files: List[str] = []
        errors: List[str] = []

        for f_info in generated_files_info:
            file_name = f_info.get("file", "")
            if not file_name:
                continue
            file_path = os.path.join(tests_dir, file_name)
            if not os.path.exists(file_path):
                errors.append(f"Validation Error: Manifest listed file '{file_name}' does not exist on disk at: {file_path}")
            else:
                test_files.append(file_path)

        # Verify registry contains appropriate validator
        validator = self._registry.get_writer(framework) if hasattr(self._registry, "get_writer") else self._registry.get_validator(framework)
        if not validator:
            raise ValueError(f"No validation engine registered for framework: '{framework}'")

        # If we have missing files errors, fail validation immediately
        if errors:
            logger.error("E2E validation failed: missing test files on disk.")
            report = ValidationReport(
                framework=framework,
                total_files=len(generated_files_info),
                compiled=False,
                tests_passed=0,
                tests_failed=0,
                tests_skipped=0,
                coverage=CoverageStats(statements=0, branches=0, functions=0, lines=0),
                quality_score=0.0,
                validation_passed=False,
                errors=errors,
                warnings=[]
            )
            self._write_reports(project_path, report)
            return report

        # 3. Execute validator
        report = validator.validate(test_files, manifest, project_path)

        # 4. Generate validation_report.json, quality_report.json, and coverage folders
        self._write_reports(project_path, report)

        return report

    def _write_reports(self, project_path: str, report: ValidationReport) -> None:
        """Write validation files and coverage reports to workspace."""
        # Write validation_report.json
        val_report_path = os.path.join(project_path, "validation_report.json")
        with open(val_report_path, "w", encoding="utf-8") as f:
            json.dump(report.model_dump(), f, indent=2)

        # Write quality_report.json
        quality_report_path = os.path.join(project_path, "quality_report.json")
        quality_data = {
            "quality_score": report.quality_score,
            "validation_passed": report.validation_passed,
            "rules_audited": {
                "compiles_cleanly": report.compiled,
                "has_cleanup_teardown_hooks": len([w for w in report.warnings if "Missing afterEach" in w]) == 0,
                "has_assertions_defined": len([w for w in report.warnings if "no expectations/expect() were called" in w]) == 0,
                "unused_imports": [w for w in report.warnings if "Unused imports" in w],
                "duplicate_tests": len([w for w in report.warnings if "Duplicate unit test titles" in w]) == 0
            },
            "warnings": report.warnings
        }
        with open(quality_report_path, "w", encoding="utf-8") as f:
            json.dump(quality_data, f, indent=2)

        # Create coverage directories
        coverage_html_dir = os.path.join(project_path, "coverage", "html")
        coverage_json_dir = os.path.join(project_path, "coverage", "json")
        os.makedirs(coverage_html_dir, exist_ok=True)
        os.makedirs(coverage_json_dir, exist_ok=True)

        # Write dummy coverage-summary.json
        cov_summary_path = os.path.join(coverage_json_dir, "coverage-summary.json")
        cov_data = {
            "total": {
                "statements": {"pct": report.coverage.statements},
                "branches": {"pct": report.coverage.branches},
                "functions": {"pct": report.coverage.functions},
                "lines": {"pct": report.coverage.lines}
            }
        }
        with open(cov_summary_path, "w", encoding="utf-8") as f:
            json.dump(cov_data, f, indent=2)

        # Write dummy index.html
        cov_html_path = os.path.join(coverage_html_dir, "index.html")
        html_content = (
            "<!DOCTYPE html>\n"
            "<html>\n"
            "<head><title>Code Coverage Report</title></head>\n"
            "<body>\n"
            f"  <h1>Code Coverage Summary ({report.framework})</h1>\n"
            "  <ul>\n"
            f"    <li>Statements: {report.coverage.statements}%</li>\n"
            f"    <li>Branches: {report.coverage.branches}%</li>\n"
            f"    <li>Functions: {report.coverage.functions}%</li>\n"
            f"    <li>Lines: {report.coverage.lines}%</li>\n"
            "  </ul>\n"
            "</body>\n"
            "</html>\n"
        )
        with open(cov_html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        logger.info("Successfully exported validation and coverage reports to workspace.")
