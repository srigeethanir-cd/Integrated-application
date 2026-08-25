"""FastAPI dependencies for Stage 1-5 workflow orchestration."""

from typing import Annotated

from fastapi import Depends

from app.dependencies.code_understanding import CodeUnderstandingServiceDependency
from app.dependencies.dependency import DependencyServiceDependency
from app.dependencies.security_scan import SecurityScanServiceDependency
from app.services.workflow_service import WorkflowService


def get_workflow_service(
    dependency_service: DependencyServiceDependency,
    security_scan_service: SecurityScanServiceDependency,
    code_understanding_service: CodeUnderstandingServiceDependency,
) -> WorkflowService:
    return WorkflowService(
        dependency_service, security_scan_service, code_understanding_service
    )


WorkflowServiceDependency = Annotated[
    WorkflowService,
    Depends(get_workflow_service),
]
