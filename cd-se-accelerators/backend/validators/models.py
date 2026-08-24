"""Validation Models and Severity Enums for the Modular Validation Framework."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ValidationSeverity(str, Enum):
    """Severity levels for validation findings."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ValidationResult(BaseModel):
    """Structured diagnostic result returned by each modular validator."""

    validator_name: str = Field(description="Name of the validator (e.g. FolderValidator, SecurityValidator)")
    passed: bool = Field(description="Validation status")
    severity: ValidationSeverity = Field(default=ValidationSeverity.LOW, description="Severity level if failed")
    recommended_fixes: List[str] = Field(default_factory=list, description="Actionable recommended fix steps")
    retry_eligible: bool = Field(default=True, description="Whether failure is eligible for automated repair retry")
    details: str = Field(description="Diagnostic details or error message")


class OverallValidationReport(BaseModel):
    """Aggregated validation report across all 10 independent validators."""

    project_name: str = Field(description="Target project name")
    total_validators: int = Field(description="Total validators executed")
    passed_count: int = Field(description="Number of passed validators")
    failed_count: int = Field(description="Number of failed validators")
    overall_passed: bool = Field(description="Whether all validators passed")
    results: List[ValidationResult] = Field(default_factory=list, description="List of individual validator results")
