"""
Pydantic models for Framework Detection (Module 2).
"""

from pydantic import BaseModel, Field, field_validator
from pathlib import Path


class FrameworkDetectRequest(BaseModel):
    """Request body for detecting the frontend framework used by a project."""

    project_path: str = Field(
        ...,
        min_length=1,
        description="Absolute or relative path to the project source directory or ZIP archive.",
        examples=[
            "/home/user/projects/my-react-app",
            "C:/Downloads/my-react-project.zip",
            "scratch/test_workspace/react_large",
        ],
    )

    @field_validator("project_path")
    @classmethod
    def validate_project_path(cls, value: str) -> str:
        path = Path(value).resolve()
        return str(path)


class FrameworkDetectResponse(BaseModel):
    """Response containing the detected framework information."""

    framework: str = Field(
        ...,
        description="Name of the detected frontend framework.",
        examples=["React", "Angular", "Next.js", "Unknown"],
    )
    confidence: int = Field(
        ...,
        ge=0,
        le=100,
        description="Confidence level of the detection (0-100).",
    )
    reason: str = Field(
        ...,
        description="Human-readable explanation for the detection result.",
    )
