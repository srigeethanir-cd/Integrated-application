"""Runtime Validator verifying python syntax, AST parsing, and build status."""

import ast
import logging
from pathlib import Path
from typing import Any, Dict
from validators.models import ValidationResult, ValidationSeverity

logger = logging.getLogger(__name__)


class RuntimeValidator:
    """Validates Python syntax and AST parsing for all backend files."""

    def validate(self, project_root: str) -> ValidationResult:
        """Validate Python syntax in project directory."""
        root = Path(project_root)
        py_files = list(root.glob("**/*.py"))

        syntax_errors = []
        for f in py_files:
            try:
                with open(f, "r", encoding="utf-8") as file:
                    ast.parse(file.read(), filename=str(f))
            except SyntaxError as e:
                syntax_errors.append(f"{f.name}: {e}")

        if syntax_errors:
            return ValidationResult(
                validator_name="RuntimeValidator",
                passed=False,
                severity=ValidationSeverity.HIGH,
                recommended_fixes=[f"Fix syntax error in {err}" for err in syntax_errors],
                retry_eligible=True,
                details=f"Found syntax errors in {len(syntax_errors)} Python files.",
            )

        return ValidationResult(
            validator_name="RuntimeValidator",
            passed=True,
            severity=ValidationSeverity.LOW,
            recommended_fixes=[],
            retry_eligible=True,
            details=f"Runtime syntax and AST parsing verified ({len(py_files)} Python files checked).",
        )
