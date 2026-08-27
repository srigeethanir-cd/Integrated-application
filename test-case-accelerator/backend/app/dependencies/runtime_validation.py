from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.database.repositories.runtime_validation_repository import RuntimeValidationRepository
from app.database.session import get_db_session
from app.dependencies.code_understanding import CodeUnderstandingRepositoryDependency
from app.dependencies.project import ProjectRepositoryDependency, StorageServiceDependency
from app.services.runtime.execution_manager import ExecutionManager
from app.services.runtime.pytest_runner import PytestRunner
from app.services.runtime.report_generator import ReportGenerator
from app.services.runtime.result_collector import ResultCollector
from app.services.runtime.runtime_validation_service import RuntimeValidationService
from app.services.runtime.openapi_metadata_service import OpenAPIMetadataService
from app.services.runtime.sut_backend_manager import SUTBackendManager
from app.services.runtime.test_file_builder import TestFileBuilder


def get_runtime_validation_repository(
    session: Annotated[Session, Depends(get_db_session)],
) -> RuntimeValidationRepository:
    return RuntimeValidationRepository(session)


RuntimeValidationRepositoryDependency = Annotated[
    RuntimeValidationRepository, Depends(get_runtime_validation_repository)
]


def get_execution_manager() -> ExecutionManager:
    return ExecutionManager(
        TestFileBuilder(), PytestRunner(), ResultCollector(), ReportGenerator()
    )


ExecutionManagerDependency = Annotated[
    ExecutionManager, Depends(get_execution_manager)
]


def get_runtime_validation_service(
    project_repository: ProjectRepositoryDependency,
    code_repository: CodeUnderstandingRepositoryDependency,
    runtime_repository: RuntimeValidationRepositoryDependency,
    storage_service: StorageServiceDependency,
    execution_manager: ExecutionManagerDependency,
) -> RuntimeValidationService:
    openapi = OpenAPIMetadataService()
    return RuntimeValidationService(
        project_repository, code_repository, runtime_repository,
        storage_service, execution_manager, openapi,
        SUTBackendManager(openapi),
    )


RuntimeValidationServiceDependency = Annotated[
    RuntimeValidationService, Depends(get_runtime_validation_service)
]
