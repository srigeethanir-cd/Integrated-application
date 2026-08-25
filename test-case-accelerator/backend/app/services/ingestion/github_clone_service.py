import re
import uuid
import time
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from git import Repo
from git.exc import GitCommandError

from app.database.models.project import Project, ProjectSourceType, ProjectStatus
from app.database.repositories.project_repository import ProjectRepository
from app.services.ingestion.storage_service import StorageService

GITHUB_OWNER_PATTERN = re.compile(
    r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?$"
)
GITHUB_REPOSITORY_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,100}$")


class GitHubCloneError(RuntimeError):
    """Raised when a public GitHub repository cannot be cloned."""


class GitHubCloneService:
    """Coordinates cloning and persistence of public GitHub projects."""

    def __init__(
        self,
        project_repository: ProjectRepository,
        storage_service: StorageService,
    ) -> None:
        self._project_repository = project_repository
        self._storage_service = storage_service

    def clone_project(
        self,
        github_url: str,
        name: str,
        description: str | None = None,
    ) -> Project:
        started_at = time.perf_counter()
        repository_url = self._validate_and_normalize_url(github_url)
        project_id = uuid.uuid4()
        project_directory = self._storage_service.create_project_directory(project_id)

        try:
            repository_directory = project_directory / "source"
            self._clone_default_branch(repository_url, repository_directory)

            from app.services.ingestion.ingestion_metadata import collect_ingestion_metadata
            collect_ingestion_metadata(
                project_id=project_id,
                project_directory=project_directory,
                source_directory=repository_directory,
                source_type="GITHUB",
                started_at=started_at,
            )

            project = Project(
                id=project_id,
                name=name,
                description=description,
                source_type=ProjectSourceType.GITHUB,
                github_url=repository_url,
                storage_path=self._storage_service.to_relative_path(
                    project_directory
                ),
                status=ProjectStatus.UPLOADED,
            )
            return self._project_repository.create(project)
        except Exception as error:
            self._cleanup_project_directory(project_id, error)
            raise

    @staticmethod
    def _validate_and_normalize_url(github_url: str) -> str:
        parsed_url = urlsplit(github_url.strip())

        if parsed_url.scheme != "https" or parsed_url.hostname not in {
            "github.com",
            "www.github.com",
        }:
            raise ValueError("GitHub URL must use HTTPS and point to github.com")

        if (
            parsed_url.username is not None
            or parsed_url.password is not None
            or parsed_url.port is not None
            or parsed_url.query
            or parsed_url.fragment
        ):
            raise ValueError("GitHub URL must not contain credentials or extra components")

        path_segments = [segment for segment in parsed_url.path.split("/") if segment]
        if len(path_segments) != 2:
            raise ValueError("GitHub URL must identify a repository")

        owner, repository = path_segments
        if repository.endswith(".git"):
            repository = repository[:-4]

        if not GITHUB_OWNER_PATTERN.fullmatch(owner):
            raise ValueError("GitHub URL contains an invalid repository owner")

        if repository in {".", ".."} or not GITHUB_REPOSITORY_PATTERN.fullmatch(
            repository
        ):
            raise ValueError("GitHub URL contains an invalid repository name")

        return urlunsplit(("https", "github.com", f"/{owner}/{repository}", "", ""))

    @staticmethod
    def _clone_default_branch(repository_url: str, destination: Path) -> None:
        try:
            with Repo.clone_from(
                repository_url,
                destination,
                depth=1,
                single_branch=True,
                env={"GIT_TERMINAL_PROMPT": "0"},
            ):
                return
        except GitCommandError as error:
            raise GitHubCloneError(
                "Unable to clone the public GitHub repository"
            ) from error

    def _cleanup_project_directory(
        self,
        project_id: uuid.UUID,
        original_error: Exception,
    ) -> None:
        try:
            self._storage_service.delete_project_directory(project_id)
        except Exception as cleanup_error:
            original_error.add_note(f"Project storage cleanup failed: {cleanup_error}")
