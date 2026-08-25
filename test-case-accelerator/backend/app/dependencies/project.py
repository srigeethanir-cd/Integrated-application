from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.database.repositories.project_repository import ProjectRepository
from app.database.session import get_db_session
from app.services.ingestion.github_clone_service import GitHubCloneService
from app.services.ingestion.project_deletion_service import ProjectDeletionService
from app.services.ingestion.storage_service import StorageService
from app.services.ingestion.upload_service import UploadService


def get_project_repository(
    session: Annotated[Session, Depends(get_db_session)],
) -> ProjectRepository:
    return ProjectRepository(session)


def get_storage_service() -> StorageService:
    return StorageService()


ProjectRepositoryDependency = Annotated[
    ProjectRepository,
    Depends(get_project_repository),
]
StorageServiceDependency = Annotated[StorageService, Depends(get_storage_service)]


def get_upload_service(
    project_repository: ProjectRepositoryDependency,
    storage_service: StorageServiceDependency,
) -> UploadService:
    return UploadService(project_repository, storage_service)


def get_github_clone_service(
    project_repository: ProjectRepositoryDependency,
    storage_service: StorageServiceDependency,
) -> GitHubCloneService:
    return GitHubCloneService(project_repository, storage_service)


def get_project_deletion_service(
    project_repository: ProjectRepositoryDependency,
    storage_service: StorageServiceDependency,
) -> ProjectDeletionService:
    return ProjectDeletionService(project_repository, storage_service)


UploadServiceDependency = Annotated[UploadService, Depends(get_upload_service)]
GitHubCloneServiceDependency = Annotated[
    GitHubCloneService,
    Depends(get_github_clone_service),
]
ProjectDeletionServiceDependency = Annotated[
    ProjectDeletionService,
    Depends(get_project_deletion_service),
]
