from __future__ import annotations

from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .enums import Category, Priority, Severity


class UnitTestSpecification(BaseModel):
    """Executable, source-grounded contract produced by Stage 4.

    The legacy descriptive fields remain on ``TestCase`` for API compatibility;
    this contract is authoritative for verification and runtime execution.
    """

    model_config = ConfigDict(extra="forbid")

    module: str
    symbol: str
    file: str
    is_async: bool = False
    parameters: list[str] = Field(default_factory=list)
    fixture_names: list[str] = Field(default_factory=list)
    patches: list[str] = Field(default_factory=list)
    arguments: dict[str, Any] = Field(default_factory=dict)
    expected_exception: str | None = None
    generated_code: str


class TestCase(BaseModel):
    """Pydantic model representing a single generated test case.

    All fields are required unless otherwise noted. The model uses ``str``
    subclasses for enumerated values to ensure JSON serialisation works out of the
    box.
    """

    id: str = Field(..., description="Unique identifier for the test case")
    title: str = Field(..., description="Short human‑readable title")
    description: str = Field(..., description="Detailed description of the test scenario")
    category: Category = Field(..., description="Test case category")
    priority: Priority = Field(..., description="Business priority of the test case")
    severity: Severity = Field(..., description="Technical severity of the defect if it occurs")
    preconditions: List[str] = Field(default_factory=list, description="List of pre‑conditions")
    steps: List[str] = Field(..., description="Ordered list of test steps")
    expected_results: List[str] = Field(..., description="Expected outcome for each step")
    requirement_ids: List[str] = Field(default_factory=list, description="Related requirement identifiers")
    business_rule_ids: List[str] = Field(default_factory=list, description="Related business rule identifiers")
    traceability: Optional[dict] = Field(default=None, description="Optional traceability metadata")
    unit_test: UnitTestSpecification | None = Field(
        default=None,
        description="Executable pytest contract for deterministic unit validation",
        exclude_if=lambda value: value is None,
    )

    model_config = ConfigDict(extra="forbid")

    @field_validator("category", mode="before")
    @classmethod
    def normalize_legacy_category(cls, value):
        mapping = {
            "functional": Category.POSITIVE,
            "performance": Category.BOUNDARY,
            "regression": Category.POSITIVE,
            "validation": Category.NEGATIVE,
            "edge_case": Category.BOUNDARY,
            "integration": Category.EXCEPTION_INTEGRATION,
            "exception": Category.EXCEPTION_INTEGRATION,
            "exception/integration": Category.EXCEPTION_INTEGRATION,
        }
        raw = value.value if isinstance(value, Category) else value
        return mapping.get(str(raw).casefold(), value)

    @field_validator("steps", "expected_results")
    @classmethod
    def non_empty_lists(cls, v: List[str]):
        if not v:
            raise ValueError("List must contain at least one element")
        return v

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str):
        if not v.strip():
            raise ValueError("Title cannot be empty")
        return v


class TestCaseBatch(BaseModel):
    """Root object requested from JSON-object-only LLM providers."""

    model_config = ConfigDict(extra="forbid")

    test_cases: List[TestCase]


class TestGenerationResult(BaseModel):
    """Persisted Stage 4 artifact appended to a Stage 3 result."""

    model_config = ConfigDict(extra="forbid")

    generated_test_cases: List[TestCase]
    coverage_summary: dict[str, float]
    total_generated: int = Field(ge=0)
    total_after_deduplication: int = Field(ge=0)
    generation_status: str = "complete"
    generation_reason: str | None = Field(
        default=None, exclude_if=lambda value: value is None
    )
    uncovered_requirements: list[dict[str, str]] = Field(default_factory=list)
