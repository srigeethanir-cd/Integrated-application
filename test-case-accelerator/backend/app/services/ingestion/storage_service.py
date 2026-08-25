import os
import shutil
import stat
import uuid
from pathlib import Path
from pathlib import PurePosixPath

from app.core.config import settings


def _remove_readonly(func, path, _):
    os.chmod(path, stat.S_IWRITE)
    func(path)



class StorageService:
    """Manages project directories within the configured storage root."""

    def __init__(self, storage_root: Path | None = None) -> None:
        configured_root = storage_root or settings.storage_root
        self._storage_root = configured_root.expanduser().resolve()
        self._storage_root.mkdir(parents=True, exist_ok=True)

    @property
    def storage_root(self) -> Path:
        return self._storage_root

    def get_project_directory(self, project_id: uuid.UUID) -> Path:
        project_directory = self._storage_root / str(project_id)
        return self._validated_project_directory(project_directory)

    def create_project_directory(self, project_id: uuid.UUID) -> Path:
        project_directory = self.get_project_directory(project_id)
        project_directory.mkdir(parents=False, exist_ok=False)
        return project_directory

    def to_relative_path(self, path: Path) -> str:
        """Return a portable storage-root-relative database path."""
        resolved_path = path.resolve(strict=False)
        if not resolved_path.is_relative_to(self._storage_root):
            raise ValueError("Storage path is outside the storage root")
        return resolved_path.relative_to(self._storage_root).as_posix()

    def resolve_project_directory(
        self,
        project_id: uuid.UUID,
        stored_path: str,
    ) -> Path:
        project_directory = self.resolve_project_path(project_id, stored_path)
        expected_directory = self.get_project_directory(project_id)
        if project_directory != expected_directory:
            raise ValueError("Stored project path does not identify the project root")
        return project_directory

    def resolve_project_path(
        self,
        project_id: uuid.UUID,
        stored_path: str,
    ) -> Path:
        """Resolve portable or legacy absolute storage paths for one project."""
        normalized_path = stored_path.strip().replace("\\", "/")
        if not normalized_path:
            raise ValueError("Stored project path is empty")

        parts = PurePosixPath(normalized_path).parts
        project_token = str(project_id)
        try:
            project_index = next(
                index
                for index, part in enumerate(parts)
                if part.lower() == project_token
            )
        except StopIteration as error:
            raise ValueError(
                "Stored path does not belong to the requested project"
            ) from error

        relative_parts = parts[project_index:]
        candidate = self._storage_root.joinpath(*relative_parts)
        resolved_candidate = self._validated_storage_directory(candidate)
        project_directory = self.get_project_directory(project_id)
        if not resolved_candidate.is_relative_to(project_directory):
            raise ValueError("Stored path escapes the managed project directory")
        return resolved_candidate

    def project_directory_exists(self, project_id: uuid.UUID) -> bool:
        project_directory = self.get_project_directory(project_id)
        return project_directory.is_dir()

    def delete_project_directory(self, project_id: uuid.UUID) -> bool:
        project_directory = self.get_project_directory(project_id)
        if not project_directory.exists():
            return False

        try:
            shutil.rmtree(project_directory, onerror=_remove_readonly)
        except FileNotFoundError:
            return False

        return True

    def stage_project_directory_for_deletion(
        self,
        project_id: uuid.UUID,
    ) -> Path | None:
        project_directory = self.get_project_directory(project_id)
        if not project_directory.exists():
            return None

        staged_directory = self._deletion_staging_directory(project_id)
        if staged_directory.exists():
            raise FileExistsError(
                f"Deletion staging directory already exists: {staged_directory}"
            )

        project_directory.rename(staged_directory)
        return staged_directory

    def restore_staged_project_directory(
        self,
        project_id: uuid.UUID,
        staged_directory: Path,
    ) -> None:
        expected_staged_directory = self._deletion_staging_directory(project_id)
        if staged_directory.resolve(strict=False) != expected_staged_directory:
            raise ValueError("Invalid staged project storage directory")

        project_directory = self.get_project_directory(project_id)
        if project_directory.exists():
            raise FileExistsError(
                f"Project storage directory already exists: {project_directory}"
            )

        staged_directory.rename(project_directory)

    def delete_staged_project_directory(
        self,
        project_id: uuid.UUID,
        staged_directory: Path,
    ) -> None:
        expected_staged_directory = self._deletion_staging_directory(project_id)
        if staged_directory.resolve(strict=False) != expected_staged_directory:
            raise ValueError("Invalid staged project storage directory")

        shutil.rmtree(staged_directory, onerror=_remove_readonly)

    def _deletion_staging_directory(self, project_id: uuid.UUID) -> Path:
        staged_directory = self._storage_root / f".deleting-{project_id}"
        return self._validated_storage_directory(staged_directory)

    def _validated_project_directory(self, project_directory: Path) -> Path:
        return self._validated_storage_directory(project_directory)

    def _validated_storage_directory(self, directory: Path) -> Path:
        if directory.is_symlink():
            raise ValueError("Project storage directory cannot be a symbolic link")

        resolved_directory = directory.resolve(strict=False)
        if not resolved_directory.is_relative_to(self._storage_root):
            raise ValueError("Project storage directory is outside the storage root")

        return resolved_directory
