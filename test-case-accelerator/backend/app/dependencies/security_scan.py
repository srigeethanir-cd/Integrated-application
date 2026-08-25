from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.repositories.security_scan_repository import SecurityScanRepository
from app.database.repositories.project_repository import ProjectRepository
from app.database.session import SessionLocal
from app.dependencies.project import StorageServiceDependency
from app.services.security_scan.security_scan_service import SemgrepRunner, SecurityScanService


def get_security_db_session():
    # Security scanning runs concurrently with dependency discovery, so it must
    # own a separate SQLAlchemy session for the request.
    with SessionLocal() as session:
        yield session


def get_security_scan_repository(
    session: Annotated[Session, Depends(get_security_db_session)],
) -> SecurityScanRepository:
    return SecurityScanRepository(session)


SecurityScanRepositoryDependency = Annotated[
    SecurityScanRepository, Depends(get_security_scan_repository)
]


def get_security_scan_service(
    session: Annotated[Session, Depends(get_security_db_session)],
    repository: SecurityScanRepositoryDependency,
    storage_service: StorageServiceDependency,
) -> SecurityScanService:
    return SecurityScanService(
        ProjectRepository(session),
        repository,
        storage_service,
        SemgrepRunner(
            executable=settings.semgrep_executable,
            config=settings.semgrep_config,
            explicit_config=settings.semgrep_explicit_config,
            metrics_enabled=settings.semgrep_metrics_enabled,
            timeout_seconds=settings.semgrep_timeout_seconds,
        ),
    )


SecurityScanServiceDependency = Annotated[
    SecurityScanService, Depends(get_security_scan_service)
]
