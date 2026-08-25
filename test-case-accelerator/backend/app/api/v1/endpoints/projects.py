import uuid
import zipfile
from typing import Annotated, NoReturn

from fastapi import (
    APIRouter,
    File,
    Form,
    HTTPException,
    Query,
    Response,
    UploadFile,
    status,
)
from sqlalchemy.exc import SQLAlchemyError

from app.dependencies.project import (
    GitHubCloneServiceDependency,
    ProjectDeletionServiceDependency,
    ProjectRepositoryDependency,
    UploadServiceDependency,
)
from app.schemas.project import (
    GitHubProjectCreateRequest,
    ProjectListResponse,
    ProjectResponse,
)
from app.services.ingestion.github_clone_service import GitHubCloneError
from app.services.ingestion.project_deletion_service import ProjectDeletionError
from app.services.ingestion.ingestion_metadata import load_ingestion_metadata

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post(
    "/upload",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a ZIP project",
    description="Store and extract a ZIP archive, then create its project record.",
)
def upload_project(
    name: Annotated[str, Form(min_length=1, max_length=255)],
    uploaded_file: Annotated[UploadFile, File(description="Project ZIP archive")],
    upload_service: UploadServiceDependency,
    description: Annotated[str | None, Form()] = None,
) -> ProjectResponse:
    try:
        project = upload_service.upload_project(
            uploaded_file=uploaded_file,
            name=name,
            description=description,
        )
    except zipfile.BadZipFile as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error
    except SQLAlchemyError as error:
        _raise_database_error(error)
    except OSError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to store the uploaded project",
        ) from error

    return _project_response(project)


@router.post(
    "/github",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Clone a GitHub project",
    description=(
        "Clone a public repository's default branch and create its project record."
    ),
)
def clone_github_project(
    request: GitHubProjectCreateRequest,
    clone_service: GitHubCloneServiceDependency,
) -> ProjectResponse:
    try:
        project = clone_service.clone_project(
            github_url=str(request.github_url),
            name=request.name,
            description=request.description,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error
    except GitHubCloneError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(error),
        ) from error
    except SQLAlchemyError as error:
        _raise_database_error(error)
    except OSError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to store the cloned project",
        ) from error

    return _project_response(project)


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Get a project",
    description="Return a project by its UUID.",
)
def get_project(
    project_id: uuid.UUID,
    project_repository: ProjectRepositoryDependency,
) -> ProjectResponse:
    try:
        project = project_repository.get_by_id(project_id)
    except SQLAlchemyError as error:
        _raise_database_error(error)

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    return _project_response(project)


@router.get(
    "",
    response_model=ProjectListResponse,
    summary="List projects",
    description="Return a paginated collection of projects.",
)
def list_projects(
    project_repository: ProjectRepositoryDependency,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> ProjectListResponse:
    try:
        projects = project_repository.get_all(skip=skip, limit=limit)
    except SQLAlchemyError as error:
        _raise_database_error(error)

    items = [_project_response(project) for project in projects]
    return ProjectListResponse(items=items, total=len(items))


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a project",
    description="Delete a project record and its managed storage directory.",
)
def delete_project(
    project_id: uuid.UUID,
    deletion_service: ProjectDeletionServiceDependency,
) -> Response:
    try:
        deleted = deletion_service.delete_project(project_id)
    except SQLAlchemyError as error:
        _raise_database_error(error)
    except (OSError, ProjectDeletionError, ValueError) as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Project deletion could not be completed consistently",
        ) from error

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _raise_database_error(error: SQLAlchemyError) -> NoReturn:
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Database operation failed",
    ) from error


def _project_response(project) -> ProjectResponse:
    return ProjectResponse.model_validate(project).model_copy(
        update={"ingestion_metadata": load_ingestion_metadata(project.id)}
    )
