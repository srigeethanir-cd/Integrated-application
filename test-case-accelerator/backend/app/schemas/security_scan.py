from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SecurityScanDiagnostic(BaseModel):
    level: str
    category: str
    type: str
    message: str
    path: str | None = None


class SecurityScanSummary(BaseModel):
    total_findings: int = 0
    by_severity: dict[str, int] = Field(default_factory=dict)
    files_scanned: int = 0
    errors: int = 0
    warnings: int = 0
    informational: int = 0
    parser_errors: int = 0
    unsupported_files: int = 0
    skipped_files: int = 0
    skipped_by_reason: dict[str, int] = Field(default_factory=dict)
    diagnostics: list[SecurityScanDiagnostic] = Field(default_factory=list)
    engine: str = "semgrep"
    engine_version: str | None = None
    duration_ms: int | None = None
    rules_executed: int | None = None
    raw_semgrep_json: dict | None = None
    security_score: int | None = None
    security_context: dict = Field(default_factory=dict)


class SecurityFindingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    rule_id: str
    severity: str
    cwe: list[str]
    owasp: list[str]
    file: str
    line: int
    start_line: int
    end_line: int
    confidence: str | None = None
    category: str | None = None
    code_snippet: str | None = None
    message: str
    recommendation: str | None = None
    references: list[str] = Field(default_factory=list)
    duplicate_count: int = 1
    metadata: dict = Field(validation_alias="semgrep_metadata")


class SecurityScanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    run_id: uuid.UUID
    project_id: uuid.UUID
    status: str
    progress_percent: int
    summary: SecurityScanSummary | None
    error_message: str | None
    retry_count: int = 0
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
    findings: list[SecurityFindingResponse] = Field(default_factory=list)
