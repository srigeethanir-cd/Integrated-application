"""
Test Execution Models – Module 10 (Execution Service).

Defines Pydantic models for representing test execution requests, test file results,
execution failures, coverage reports, and overall test execution status summaries.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TestExecutionRequest(BaseModel):
    """Payload to request/trigger test execution for a given pipeline run."""

    pipeline_run_id: str = Field(..., description="Unique pipeline run identifier.")


class CoverageReport(BaseModel):
    """Coverage statistics for statements, branches, functions, and lines."""

    statements: float = Field(..., description="Percentage of statement coverage.")
    branches: float = Field(..., description="Percentage of branch coverage.")
    functions: float = Field(..., description="Percentage of function coverage.")
    lines: float = Field(..., description="Percentage of line coverage.")
    coverage_status: Optional[str] = Field(None, description="Optional status message, e.g. 'unavailable'.")


class TestFileResult(BaseModel):
    """Detailed summary of execution results for a single test suite file."""

    file_name: str = Field(..., description="Name of the test file.")
    file_path: str = Field(..., description="Relative or absolute path of the test file.")
    framework: str = Field(..., description="Frontend framework (React/Angular).")
    component: str = Field(..., description="Associated component name.")
    total_tests: int = Field(..., description="Total tests run in this file.")
    passed: int = Field(..., description="Passed tests count.")
    failed: int = Field(..., description="Failed tests count.")
    skipped: int = Field(..., description="Skipped tests count.")
    test_case_ids: List[str] = Field(default_factory=list, description="IDs of test cases represented in this file.")


class TestFailure(BaseModel):
    """Detail of a single failing test assertion or compilation error."""

    test_case_id: Optional[str] = Field(None, description="Associated Test Case ID.")
    edge_case_id: Optional[str] = Field(None, description="Associated Edge Case ID.")
    strategy_id: Optional[str] = Field(None, description="Associated Strategy ID.")
    component_id: Optional[str] = Field(None, description="Associated Component ID.")
    file_name: str = Field(..., description="File where failure occurred.")
    test_name: str = Field(..., description="Name/title of the test that failed.")
    error_message: str = Field(..., description="Detailed assertion or error message.")
    stack_trace: Optional[str] = Field(None, description="Detailed traceback/stack trace from execution.")
    expected: Optional[str] = Field(None, description="Expected outcome/value.")
    received: Optional[str] = Field(None, description="Received outcome/value.")
    line_number: Optional[str] = Field(None, description="Line number where failure occurred.")


class TestExecutionReport(BaseModel):
    """Summary of overall test execution results across all test suite files."""

    pipeline_run_id: str = Field(..., description="Associated pipeline run ID.")
    status: str = Field(..., description="Execution status, e.g. 'completed', 'failed'.")
    framework: str = Field(..., description="Frontend framework (React/Angular).")
    total_tests: int = Field(..., description="Total tests executed across all files.")
    passed: int = Field(..., description="Total passed tests.")
    failed: int = Field(..., description="Total failed tests.")
    skipped: int = Field(..., description="Total skipped tests.")
    pass_rate: float = Field(..., description="Percentage of passed tests.")
    execution_time_ms: float = Field(..., description="Total execution time in milliseconds.")
    coverage: Optional[CoverageReport] = Field(None, description="Code coverage statistics, if available.")
    test_files: List[TestFileResult] = Field(default_factory=list, description="List of file-level test outcomes.")
    failures: List[TestFailure] = Field(default_factory=list, description="List of individual test failures.")
