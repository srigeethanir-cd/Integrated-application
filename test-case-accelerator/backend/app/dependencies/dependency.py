"""FastAPI dependency providers for Stage 2."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.database.repositories.dependency_repository import DependencyRepository
from app.database.session import get_db_session
from app.dependencies.project import (
    ProjectRepositoryDependency,
    StorageServiceDependency,
)
from app.services.dependency.dependency_service import DependencyService
from app.services.dependency.backend_filter import BackendFilter
from app.services.dependency.dependency_graph import DependencyGraph
from app.services.dependency.import_resolver import ImportResolver
from app.services.dependency.metadata_service import MetadataService
from app.services.dependency.project_traverser import ProjectTraverser
from app.infrastructure.redis import CacheManager, get_cache_manager


def get_dependency_repository(
    session: Annotated[Session, Depends(get_db_session)],
) -> DependencyRepository:
    return DependencyRepository(session)


DependencyRepositoryDependency = Annotated[
    DependencyRepository, Depends(get_dependency_repository)
]


def get_dependency_service(
    project_repository: ProjectRepositoryDependency,
    dependency_repository: DependencyRepositoryDependency,
    storage_service: StorageServiceDependency,
    cache_manager: Annotated[CacheManager, Depends(get_cache_manager)],
) -> DependencyService:
    return DependencyService(
        project_repository=project_repository,
        dependency_repository=dependency_repository,
        storage_service=storage_service,
        traverser=ProjectTraverser(
            ignore_patterns=[
                ".git/**", "node_modules/**", ".venv/**", "venv/**",
                "__pycache__/**", "dist/**", "build/**",
            ]
        ),
        import_resolver=ImportResolver(),
        graph_builder=DependencyGraph(),
        backend_filter=BackendFilter(),
        metadata_service=MetadataService(),
        cache_manager=cache_manager,
    )


DependencyServiceDependency = Annotated[
    DependencyService, Depends(get_dependency_service)
]
