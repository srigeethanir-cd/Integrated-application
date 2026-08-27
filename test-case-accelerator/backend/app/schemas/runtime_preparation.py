"""Artifacts produced between quality optimization and runtime validation."""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class RuntimePreparationIssue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    test_case_id: str
    code: str
    message: str


class RuntimeTestClassification(StrEnum):
    HTTP = "HTTP"
    UNIT = "UNIT"
    INTEGRATION = "INTEGRATION"
    NON_HTTP = "NON_HTTP"


class RuntimeExecutionTarget(BaseModel):
    model_config = ConfigDict(extra="forbid")

    test_case_id: str
    classification: RuntimeTestClassification | None = None
    route: str | None = None
    http_method: str | None = None
    expected_http_status: int | None = None
    path_parameters: dict[str, Any] = Field(default_factory=dict)
    query_parameters: dict[str, Any] = Field(default_factory=dict)
    required_headers: dict[str, str] = Field(default_factory=dict)
    authentication_required: bool | None = False
    authentication_schemes: list[str] = Field(default_factory=list)
    request_payload: Any | None = None
    expected_response: Any | None = None
    expected_response_fields: list[str] = Field(default_factory=list)
    executable: bool = False
    traceability: dict[str, Any] = Field(default_factory=dict)
    issues: list[RuntimePreparationIssue] = Field(default_factory=list)
    module: str | None = None
    symbol: str | None = None
    generated_code: str | None = None


class RuntimeExecutionPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    targets: list[RuntimeExecutionTarget]
    issues: list[RuntimePreparationIssue] = Field(default_factory=list)
    total_tests: int = Field(ge=0)
    prepared_tests: int = Field(ge=0)
    unresolved_tests: int = Field(ge=0)
