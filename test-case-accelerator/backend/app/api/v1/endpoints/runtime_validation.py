import uuid
import logging

from fastapi import APIRouter, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from app.database.schema_validation import DatabaseSchemaOutdatedError

from app.dependencies.runtime_validation import RuntimeValidationServiceDependency
from app.schemas.runtime_validation import (
    RuntimeValidationReport,
    RuntimeValidationRequest,
    RuntimeValidationRunResponse,
)
from app.services.runtime.runtime_validation_service import (
    RuntimeArtifactNotReadyError,
    RuntimeProjectNotFoundError,
    RuntimeSourceRunNotFoundError,
    RuntimeValidationRunNotFoundError,
)

router = APIRouter(tags=["runtime-validation"])
logger = logging.getLogger(__name__)


@router.post(
    "/projects/{project_id}/runtime-validation",
    response_model=RuntimeValidationRunResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_runtime_validation(
    project_id: uuid.UUID,
    request: RuntimeValidationRequest,
    service: RuntimeValidationServiceDependency,
) -> RuntimeValidationRunResponse:
    try:
        run = service.run(
            project_id=project_id,
            code_understanding_run_id=request.code_understanding_run_id,
            base_url=str(request.base_url).rstrip("/"),
            test_case_ids=request.test_case_ids,
            timeout_seconds=request.timeout_seconds,
        )
        return _run_response(run)
    except (RuntimeProjectNotFoundError, RuntimeSourceRunNotFoundError) as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error
    except RuntimeArtifactNotReadyError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error
    except DatabaseSchemaOutdatedError as error:
        logger.exception("Runtime Validation blocked by an outdated database schema")
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "Runtime Validation database schema is outdated. "
            f"Expected Alembic revision {error.expected_revision}.",
        ) from error
    except SQLAlchemyError as error:
        logger.exception("Runtime Validation database operation failed")
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "Runtime Validation database operation failed. See server logs for details.",
        ) from error
    except (OSError, ValueError) as error:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Runtime validation failed") from error


@router.get(
    "/runtime-validations/{run_id}", response_model=RuntimeValidationRunResponse
)
def get_runtime_validation(
    run_id: uuid.UUID, service: RuntimeValidationServiceDependency,
) -> RuntimeValidationRunResponse:
    try:
        return _run_response(service.get_run(run_id))
    except RuntimeValidationRunNotFoundError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error


@router.get(
    "/runtime-validations/{run_id}/report", response_model=RuntimeValidationReport
)
def get_runtime_validation_report(
    run_id: uuid.UUID, service: RuntimeValidationServiceDependency,
) -> RuntimeValidationReport:
    try:
        return service.get_report(run_id)
    except RuntimeValidationRunNotFoundError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error
    except RuntimeArtifactNotReadyError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error


def _run_response(run) -> RuntimeValidationRunResponse:
    return RuntimeValidationRunResponse(
        run_id=run.id,
        project_id=run.project_id,
        source_stage_run_id=run.source_stage_run_id,
        status=run.status,
        execution_mode=run.execution_mode,
        base_url=run.base_url,
        duration_ms=run.duration_ms,
        summary=run.summary,
        error_message=run.error_message,
        created_at=run.created_at,
        started_at=run.started_at,
        finished_at=run.finished_at,
    )
