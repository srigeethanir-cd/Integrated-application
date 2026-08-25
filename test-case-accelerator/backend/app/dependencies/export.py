"""Dependency providers for pytest suite exports."""

from typing import Annotated

from fastapi import Depends

from app.core.config import settings
from app.dependencies.code_understanding import CodeUnderstandingServiceDependency
from app.dependencies.project import ProjectRepositoryDependency
from app.services.export import PytestExportService


def get_pytest_export_service() -> PytestExportService:
    return PytestExportService(generator_version=settings.app_version)


PytestExportServiceDependency = Annotated[
    PytestExportService,
    Depends(get_pytest_export_service),
]

__all__ = [
    "CodeUnderstandingServiceDependency",
    "ProjectRepositoryDependency",
    "PytestExportServiceDependency",
]
