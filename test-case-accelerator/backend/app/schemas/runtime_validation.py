from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from app.database.models.runtime_validation import (
    RuntimeTestStatus,
    RuntimeValidationStatus,
)


class RuntimeValidationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code_understanding_run_id: uuid.UUID | None = None
    base_url: HttpUrl = "http://127.0.0.1:8001"
    test_case_ids: list[str] | None = None
    timeout_seconds: int = Field(default=120, ge=1, le=1800)


class RuntimeExecutionResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    test_case_id: str
    runtime_status: RuntimeTestStatus
    expected_result: dict[str, Any] | None = None
    actual_result: dict[str, Any] | None = None
    assertion_failure: str | None = None
    logs: str | None = None
    execution_time_ms: float = 0


class RuntimeValidationRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    run_id: uuid.UUID
    project_id: uuid.UUID
    source_stage_run_id: uuid.UUID
    status: RuntimeValidationStatus
    execution_mode: str
    base_url: str
    duration_ms: float | None = None
    summary: dict[str, Any] | None = None
    error_message: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None


class RuntimeValidationReport(BaseModel):
    run_id: uuid.UUID
    project_id: uuid.UUID
    source_stage_run_id: uuid.UUID
    status: RuntimeValidationStatus
    summary: dict[str, Any]
    pass_rate: float
    duration_ms: float
    failed_tests: list[str]
    skipped_tests: list[str]
    results: list[RuntimeExecutionResultResponse]
