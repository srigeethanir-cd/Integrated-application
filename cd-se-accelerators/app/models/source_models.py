"""
Pydantic models for Source Ingestion (Module 1).
"""

from typing import Optional
from pathlib import Path
from pydantic import BaseModel, Field, field_validator


class LocalProjectRequest(BaseModel):
    """Request body for registering a local project path."""

    project_path: str = Field(
        ...,
        min_length=1,
        description="Absolute path to an existing local project directory.",
        examples=["/home/user/projects/my-react-app"],
    )

    @field_validator("project_path")
    @classmethod
    def validate_project_path(cls, value: str) -> str:
        path = Path(value)
        if not path.is_absolute():
            raise ValueError("project_path must be an absolute path.")
        return value


class GitCloneRequest(BaseModel):
    """Request body for cloning a Git repository."""

    repo_url: str = Field(
        ...,
        min_length=1,
        description="URL of the Git repository to clone.",
        examples=["https://github.com/user/repo.git"],
    )

    @field_validator("repo_url")
    @classmethod
    def validate_repo_url(cls, value: str) -> str:
        if not value.startswith(("https://", "http://", "git@")):
            raise ValueError(
                "repo_url must start with https://, http://, or git@."
            )
        return value


class IngestionStats(BaseModel):
    """File counts breakdown during source ingestion."""

    total_files: int = Field(0, description="Total files found in archive.")
    ignored_files: int = Field(0, description="Files skipped during filtering.")
    extracted_files: int = Field(0, description="Files extracted to workspace.")
    processed_files: int = Field(0, description="Relevant source files indexed.")


class IngestionPerformanceMetrics(BaseModel):
    """Performance timing measurements during ingestion in milliseconds."""

    upload_time_ms: float = Field(0.0, description="Time to process raw upload bytes.")
    zip_inspection_time_ms: float = Field(0.0, description="Time to inspect ZIP directory structure.")
    file_filtering_time_ms: float = Field(0.0, description="Time to filter out unnecessary files.")
    framework_detection_time_ms: float = Field(0.0, description="Time for early deterministic framework detection.")
    extraction_time_ms: float = Field(0.0, description="Time to selectively extract relevant files.")
    project_index_time_ms: float = Field(0.0, description="Time to construct project index.")
    total_ingestion_time_ms: float = Field(0.0, description="Total source ingestion duration.")


class SourceIngestionResponse(BaseModel):
    """Response returned after a successful source ingestion operation."""

    project_id: str = Field(
        ..., description="Unique identifier for the ingested project."
    )
    project_path: str = Field(
        ..., description="Absolute path to the project source directory."
    )
    message: str = Field(
        ..., description="Human-readable status message."
    )
    detected_framework: Optional[str] = Field(
        None, description="Early detected frontend framework (React, Angular, Next.js, or Unknown)."
    )
    stats: Optional[IngestionStats] = Field(
        None, description="File counts statistics during ingestion."
    )
    metrics: Optional[IngestionPerformanceMetrics] = Field(
        None, description="Detailed ingestion performance timing metrics."
    )
