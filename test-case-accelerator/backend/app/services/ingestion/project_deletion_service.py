import uuid
from pathlib import Path

from app.database.repositories.project_repository import ProjectRepository
from app.services.ingestion.storage_service import StorageService


class ProjectDeletionError(RuntimeError):
    """Raised when a coordinated project deletion cannot be completed."""


class ProjectDeletionService:
    """Coordinates recoverable deletion of project records and storage."""

    def __init__(
        self,
        project_repository: ProjectRepository,
        storage_service: StorageService,
    ) -> None:
        self._project_repository = project_repository
        self._storage_service = storage_service

    def delete_project(self, project_id: uuid.UUID) -> bool:
        project = self._project_repository.get_by_id(project_id)
        if project is None:
            return False

        staged_directory = self._storage_service.stage_project_directory_for_deletion(
            project_id
        )

        try:
            deleted_project = self._project_repository.delete(
                project_id,
                commit=False,
            )
        except Exception as error:
            self._rollback_database(error)
            self._restore_storage(project_id, staged_directory, error)
            raise

        if deleted_project is None:
            self._restore_storage(project_id, staged_directory)
            return False

        if staged_directory is not None:
            try:
                self._storage_service.delete_staged_project_directory(
                    project_id,
                    staged_directory,
                )
            except Exception as error:
                self._rollback_database(error)
                self._restore_storage(project_id, staged_directory, error)
                raise ProjectDeletionError(
                    "Project deletion failed and was rolled back"
                ) from error

        self._project_repository.commit()
        return True

    def _restore_storage(
        self,
        project_id: uuid.UUID,
        staged_directory: Path | None,
        original_error: Exception | None = None,
    ) -> None:
        if staged_directory is None:
            return

        try:
            self._storage_service.restore_staged_project_directory(
                project_id,
                staged_directory,
            )
        except Exception as recovery_error:
            if original_error is None:
                raise
            original_error.add_note(
                f"Project storage recovery failed: {recovery_error}"
            )

    def _rollback_database(self, original_error: Exception) -> None:
        try:
            self._project_repository.rollback()
        except Exception as recovery_error:
            original_error.add_note(
                f"Project database rollback failed: {recovery_error}"
            )
