"""Stage 2 dependency discovery API."""

import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError

from app.dependencies.dependency import DependencyServiceDependency
from app.schemas.dependency import DependencyResponse, DependencyRunDetail
from app.services.dependency.dependency_service import (
    NoSupportedSourceFilesError,
)
from app.services.dependency.analysis_summary import build_dependency_analysis

router = APIRouter(tags=["dependencies"])


@router.post(
    "/projects/{project_id}/dependencies",
    response_model=DependencyResponse,
    status_code=status.HTTP_201_CREATED,
)
def discover_dependencies(
    project_id: uuid.UUID,
    dependency_service: DependencyServiceDependency,
) -> DependencyResponse:
    try:
        run = dependency_service.run(project_id)
    except NoSupportedSourceFilesError as error:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            str(error),
        ) from error
    except FileNotFoundError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error
    except ValueError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error
    except (OSError, SQLAlchemyError) as error:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Dependency discovery failed",
        ) from error
    if run is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")
    return DependencyResponse(run_id=run.id, status=run.status)


@router.get(
    "/dependency-runs/{run_id}",
    response_model=DependencyRunDetail,
)
def get_dependency_run(
    run_id: uuid.UUID,
    dependency_service: DependencyServiceDependency,
) -> DependencyRunDetail:
    try:
        run = dependency_service.get_run(run_id)
    except SQLAlchemyError as error:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "Database operation failed",
        ) from error
    if run is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Dependency run not found")
    return DependencyRunDetail(
        run_id=run.id,
        project_id=run.project_id,
        project_path=run.project_path,
        status=run.status,
        files=run.files,
        analysis=build_dependency_analysis(run.files),
    )


@router.get(
    "/projects/{project_id}/dependency-runs/latest",
    response_model=DependencyRunDetail,
)
def get_latest_dependency_run(
    project_id: uuid.UUID,
    dependency_service: DependencyServiceDependency,
) -> DependencyRunDetail:
    try:
        run = dependency_service.get_latest_run(project_id)
    except SQLAlchemyError as error:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "Database operation failed",
        ) from error
    if run is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Dependency run not found")
    return DependencyRunDetail(
        run_id=run.id,
        project_id=run.project_id,
        project_path=run.project_path,
        status=run.status,
        files=run.files,
        analysis=build_dependency_analysis(run.files),
    )
