import uuid
from typing import Any
from datetime import datetime
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, HttpUrl

from app.database.models.project import ProjectSourceType, ProjectStatus


def _validate_github_url(url: HttpUrl) -> HttpUrl:
    if url.scheme != "https":
        raise ValueError("GitHub URL must use HTTPS")

    if url.host not in {"github.com", "www.github.com"}:
        raise ValueError("URL must point to github.com")

    path_segments = [segment for segment in url.path.split("/") if segment]
    if len(path_segments) < 2:
        raise ValueError("GitHub URL must identify a repository")

    return url


GitHubUrl = Annotated[
    HttpUrl,
    Field(max_length=2048),
    AfterValidator(_validate_github_url),
]


class ProjectBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=255)
    description: str | None = None


class GitHubProjectCreateRequest(ProjectBase):
    github_url: GitHubUrl


class ProjectUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    github_url: GitHubUrl | None = None


class ProjectResponse(ProjectBase):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: uuid.UUID
    source_type: ProjectSourceType
    github_url: GitHubUrl | None
    storage_path: str
    status: ProjectStatus
    created_at: datetime
    updated_at: datetime
    ingestion_metadata: dict[str, Any] | None = None


class ProjectListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[ProjectResponse]
    total: int = Field(ge=0)
