"""End-to-end Stage 1-5 workflow endpoints."""

import uuid
import zipfile
from typing import Annotated, Callable

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from openai import OpenAIError
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.agents.code_understanding.client import StructuredOutputClientError
from app.agents.test_generation.test_generation_agent import TestGenerationError
from app.agents.semantic_verification.agent import TestVerificationError
from app.dependencies.project import (
    GitHubCloneServiceDependency,
    UploadServiceDependency,
    ProjectRepositoryDependency,
)
from app.dependencies.workflow import WorkflowServiceDependency
from app.schemas.project import GitHubProjectCreateRequest, ProjectResponse
from app.schemas.workflow import (
    WorkflowContinueRequest,
    WorkflowResponse,
    WorkflowResumeRequest,
)
from app.services.dependency.dependency_service import NoSupportedSourceFilesError
from app.services.code_understanding.code_understanding_service import (
    CodeUnderstandingError,
)
from app.services.code_understanding.public_artifact import public_pipeline_result
from app.services.ingestion.github_clone_service import GitHubCloneError
from app.services.workflow_service import WorkflowError, WorkflowResult
from app.services.security_scan import SecurityScanError
from app.services.dependency.analysis_summary import build_dependency_analysis
from app.services.ingestion.ingestion_metadata import load_ingestion_metadata
from app.api.v1.endpoints.security_scans import _response as security_response

router = APIRouter(prefix="/workflows", tags=["workflows"])


@router.post(
    "/upload",
    response_model=WorkflowResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a ZIP project and run through Stage 4",
)
def run_upload_workflow(
    name: Annotated[str, Form(min_length=1, max_length=255)],
    uploaded_file: Annotated[UploadFile, File(description="Project ZIP archive")],
    upload_service: UploadServiceDependency,
    workflow_service: WorkflowServiceDependency,
    description: Annotated[str | None, Form()] = None,
) -> WorkflowResponse:
    return _execute_workflow(
        lambda: upload_service.upload_project(
            uploaded_file=uploaded_file,
            name=name,
            description=description,
        ),
        workflow_service,
    )


@router.post(
    "/github",
    response_model=WorkflowResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Import a GitHub project and run through Stage 4",
)
def run_github_workflow(
    request: GitHubProjectCreateRequest,
    clone_service: GitHubCloneServiceDependency,
    workflow_service: WorkflowServiceDependency,
) -> WorkflowResponse:
    return _execute_workflow(
        lambda: clone_service.clone_project(
            github_url=str(request.github_url),
            name=request.name,
            description=request.description,
        ),
        workflow_service,
    )


@router.post(
    "/{project_id}/resume",
    response_model=WorkflowResponse,
    summary="Resume pipeline execution for a project",
)
def resume_workflow(
    project_id: uuid.UUID,
    project_repository: ProjectRepositoryDependency,
    workflow_service: WorkflowServiceDependency,
    request: WorkflowResumeRequest | None = None,
) -> WorkflowResponse:
    project = project_repository.get_by_id(project_id)
    if project is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")
    
    try:
        if request is None:
            return _response(workflow_service.resume(project))
        return _response(workflow_service.resume(
            project,
            start_stage=request.start_stage,
            force=request.force,
        ))
    except (zipfile.BadZipFile, ValueError, NoSupportedSourceFilesError) as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(error)) from error
    except (GitHubCloneError, OpenAIError, StructuredOutputClientError) as error:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY, "Workflow provider failed"
        ) from error
    except (TestGenerationError, TestVerificationError) as error:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY, "Workflow provider failed"
        ) from error
    except (WorkflowError, CodeUnderstandingError, SecurityScanError, FileNotFoundError) as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error
    except SQLAlchemyError as error:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, "Database operation failed"
        ) from error
    except (OSError, ValidationError) as error:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR, "Workflow failed"
        ) from error


@router.get(
    "/{project_id}/state",
    response_model=WorkflowResponse,
    summary="Load persisted approval workflow state",
)
def get_workflow_state(
    project_id: uuid.UUID,
    project_repository: ProjectRepositoryDependency,
    workflow_service: WorkflowServiceDependency,
) -> WorkflowResponse:
    project = project_repository.get_by_id(project_id)
    if project is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")
    return _response(workflow_service.state(project))


@router.post(
    "/{project_id}/continue",
    response_model=WorkflowResponse,
    summary="Approve and execute exactly one next stage",
)
def continue_workflow(
    project_id: uuid.UUID,
    request: WorkflowContinueRequest,
    project_repository: ProjectRepositoryDependency,
    workflow_service: WorkflowServiceDependency,
) -> WorkflowResponse:
    project = project_repository.get_by_id(project_id)
    if project is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")
    try:
        return _response(workflow_service.continue_from(project, request.from_stage))
    except (NoSupportedSourceFilesError, ValueError) as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(error)) from error
    except (OpenAIError, StructuredOutputClientError, SecurityScanError) as error:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(error)) from error
    except (WorkflowError, CodeUnderstandingError, FileNotFoundError) as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error
    except SQLAlchemyError as error:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, "Database operation failed"
        ) from error
    except (OSError, ValidationError) as error:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, str(error)) from error


def _execute_workflow(
    ingest: Callable,
    workflow_service: WorkflowServiceDependency,
) -> WorkflowResponse:
    try:
        project = ingest()
        return _response(workflow_service.run_through_stage_four(project))
    except (zipfile.BadZipFile, ValueError, NoSupportedSourceFilesError) as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(error)) from error
    except (GitHubCloneError, OpenAIError, StructuredOutputClientError) as error:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY, "Workflow provider failed"
        ) from error
    except (TestGenerationError, TestVerificationError) as error:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY, "Workflow provider failed"
        ) from error
    except (WorkflowError, CodeUnderstandingError, SecurityScanError, FileNotFoundError) as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error
    except SQLAlchemyError as error:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, "Database operation failed"
        ) from error
    except (OSError, ValidationError) as error:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR, "Workflow failed"
        ) from error


def _response(result: WorkflowResult) -> WorkflowResponse:
    run = result.code_understanding_run
    return WorkflowResponse(
        project=ProjectResponse.model_validate(result.project).model_copy(
            update={
                "ingestion_metadata": load_ingestion_metadata(result.project.id)
            }
        ),
        current_stage=result.current_stage,
        status=result.status,
        completed_stage=result.completed_stage,
        next_stage=result.next_stage,
        security_scan=(
            security_response(result.security_scan_run)
            if result.security_scan_run is not None else None
        ),
        dependency=(
            {
                "run_id": result.dependency_run.id,
                "project_id": result.dependency_run.project_id,
                "project_path": result.dependency_run.project_path,
                "status": result.dependency_run.status,
                "files": result.dependency_run.files,
                "analysis": build_dependency_analysis(result.dependency_run.files),
            }
            if result.dependency_run is not None else None
        ),
        pipeline=(
            {
                "run_id": run.id,
                "status": run.status,
                "result": public_pipeline_result(run.result),
                "failed_stage": run.failed_stage,
                "failure_reason": run.failure_reason,
                "retry_count": run.retry_count,
                "last_successful_stage": run.last_successful_stage,
            }
            if run is not None else None
        ),
        generation=result.test_generation,
        error=result.error,
        logs=list(result.logs),
    )
