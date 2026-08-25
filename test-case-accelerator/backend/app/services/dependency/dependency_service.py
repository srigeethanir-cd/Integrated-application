"""Orchestration for Stage 2 dependency discovery."""

from __future__ import annotations

import uuid
from pathlib import Path

from app.database.models.dependency import DependencyRun
from app.database.models.project import ProjectStatus
from app.database.repositories.dependency_repository import DependencyRepository
from app.database.repositories.project_repository import ProjectRepository
from app.services.ingestion.storage_service import StorageService
from app.infrastructure.redis import CacheManager

from .backend_filter import BackendFilter
from .dependency_graph import DependencyGraph
from .import_resolver import ImportResolver
from .metadata_service import MetadataService
from .project_traverser import ProjectTraverser


class NoSupportedSourceFilesError(ValueError):
    """Raised when Stage 2 finds no source files it can analyze."""


class DependencyService:
    def __init__(
        self,
        project_repository: ProjectRepository,
        dependency_repository: DependencyRepository,
        storage_service: StorageService,
        traverser: ProjectTraverser,
        import_resolver: ImportResolver,
        graph_builder: DependencyGraph,
        backend_filter: BackendFilter,
        metadata_service: MetadataService,
        cache_manager: CacheManager | None = None,
    ) -> None:
        self._project_repository = project_repository
        self._dependency_repository = dependency_repository
        self._storage_service = storage_service
        self._traverser = traverser
        self._import_resolver = import_resolver
        self._graph_builder = graph_builder
        self._backend_filter = backend_filter
        self._metadata_service = metadata_service
        self._cache_manager = cache_manager

    def run(self, project_id: uuid.UUID) -> DependencyRun | None:
        project = self._project_repository.get_by_id(project_id)
        if project is None:
            return None
        if self._cache_manager is not None:
            self._cache_manager.clear_project(str(project.id))

        project_directory = self._storage_service.resolve_project_directory(
            project_id,
            project.storage_path,
        )
        source_directory = project_directory / "source"

        run = self._dependency_repository.create_run(
            project_id=project.id,
            project_path=self._storage_service.to_relative_path(source_directory),
        )
        try:
            self._project_repository.update_status(
                project.id,
                ProjectStatus.PROCESSING,
            )
            files = self._backend_filter.filter(list(self._traverser.scan(source_directory)))
            if not files:
                raise NoSupportedSourceFilesError(
                    "No supported source files were found in the repository."
                )
            metadata = [
                item.model_copy(
                    update={
                        "path": self._storage_service.to_relative_path(
                            Path(item.path)
                        )
                    }
                )
                for item in self._metadata_service.generate(files)
            ]
            edges = [
                (str(file_path), str(resolved_path))
                for file_path in files
                for _, resolved_path in self._import_resolver.resolve(
                    file_path, project_root=source_directory
                )
                if resolved_path is not None
            ]
            self._graph_builder.add_edges(edges)
            self._dependency_repository.complete(run, metadata)
            self._project_repository.update_status(project.id, ProjectStatus.READY)
        except Exception:
            self._dependency_repository.fail(run)
            self._project_repository.update_status(project.id, ProjectStatus.FAILED)
            raise
        return run

    def get_run(self, run_id: uuid.UUID) -> DependencyRun | None:
        return self._dependency_repository.get_by_id(run_id)

    def get_latest_run(self, project_id: uuid.UUID) -> DependencyRun | None:
        return self._dependency_repository.get_latest_completed_by_project_id(
            project_id
        )

    def get_latest_workflow_run(self, project_id: uuid.UUID) -> DependencyRun | None:
        """Return the latest Stage 2 attempt, including failed attempts."""
        return self._dependency_repository.get_latest_by_project_id(project_id)
