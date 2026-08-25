"""
Test Writer Models – Module 8.

Defines Pydantic schemas for generating framework-specific test suites,
writing them to output workspaces, and reporting compilation syntax errors.
"""

from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field

from app.models.ir_models import FrameworkAgnosticIR
from app.models.test_case_models import TestCasePlanResponse


# TestWriterRequest directly accepts TestCasePlanResponse without a wrapper.
TestWriterRequest = TestCasePlanResponse


class GeneratedTestFile(BaseModel):
    """Details of a single generated framework test file."""

    file_name: str = Field(..., description="Name of the generated test file.")
    file_path: str = Field(..., description="Absolute file path location.")
    content: str = Field(..., description="Complete compiled file source code content.")
    test_case_ids: List[str] = Field(default_factory=list, description="List of test case IDs compiled inside this file.")
    component: Optional[str] = Field(None, description="Name of the component under test.")
    source_file: Optional[str] = Field(None, description="Source component file path.")
    source_language: Optional[str] = Field(None, description="Source language: JavaScript or TypeScript.")
    source_extension: Optional[str] = Field(None, description="Source file extension: .jsx, .js, .tsx, or .ts.")
    test_extension: Optional[str] = Field(None, description="Generated test file extension: .test.jsx, .test.js, .test.tsx, or .test.ts.")


class TestWriterResponse(BaseModel):
    """Summary of the code generation, formatting, and validation results."""

    total_files: int = Field(0, ge=0, description="Total number of test files generated.")
    generated_files: List[GeneratedTestFile] = Field(default_factory=list, description="Details of the generated files.")
    manifest_path: str = Field(..., description="Path to the created test_manifest.json.")
    validation_passed: bool = Field(..., description="True if code formatting and AST syntax compiler checks passed.")
    validation_errors: List[str] = Field(default_factory=list, description="Detail list of parsing or syntax validation errors.")
