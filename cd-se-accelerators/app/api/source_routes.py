"""
API routes for Source Ingestion (Module 1).

All business logic lives in ``SourceIngestionService``; these handlers only
translate HTTP concerns (status codes, multipart parsing) into service calls.
"""

import logging

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.models.source_models import (
    GitCloneRequest,
    LocalProjectRequest,
    SourceIngestionResponse,
)
from app.services.source_ingestion_service import SourceIngestionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/source", tags=["Source Ingestion"])

# Service instance – in a larger app this would come from a DI container.
_service = SourceIngestionService()


@router.post(
    "/upload",
    response_model=SourceIngestionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a ZIP archive",
    description="Upload a .zip file containing a frontend project. "
    "The archive is inspected, filtered, and selectively extracted into a new isolated workspace.",
)
async def upload_zip(file: UploadFile = File(...)) -> SourceIngestionResponse:
    """Accept a multipart ZIP upload."""
    if file.filename is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must have a filename.",
        )

    try:
        file_bytes = await file.read()
        res = await _service.upload_zip(
            file.filename, file_bytes
        )
    except ValueError as exc:
        logger.warning("ZIP upload validation failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        )
    except Exception as exc:
        logger.exception("ZIP upload failed unexpectedly")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process ZIP upload: {exc}",
        )

    return SourceIngestionResponse(
        project_id=res.project_id,
        project_path=res.project_path,
        message=f"ZIP archive uploaded and selectively extracted ({res.detected_framework} project detected).",
        detected_framework=res.detected_framework,
        stats=getattr(res, "stats", None),
        metrics=getattr(res, "metrics", None),
    )


@router.post(
    "/local",
    response_model=SourceIngestionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a local project",
    description="Register an existing local directory as a project. "
    "The directory contents are copied into a new workspace skipping ignored folders.",
)
async def register_local(
    request: LocalProjectRequest,
) -> SourceIngestionResponse:
    """Register a local project path."""
    try:
        res = await _service.register_local_project(
            request.project_path
        )
    except ValueError as exc:
        logger.warning("Local project validation failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        )
    except Exception as exc:
        logger.exception("Local project registration failed unexpectedly")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register local project: {exc}",
        )

    return SourceIngestionResponse(
        project_id=res.project_id,
        project_path=res.project_path,
        message="Local project registered successfully.",
        detected_framework=getattr(res, "detected_framework", None),
        stats=getattr(res, "stats", None),
        metrics=getattr(res, "metrics", None),
    )


@router.post(
    "/git",
    response_model=SourceIngestionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Clone a Git repository",
    description="Clone a remote Git repository into a new workspace.",
)
async def clone_git(request: GitCloneRequest) -> SourceIngestionResponse:
    """Clone a remote Git repository."""
    try:
        res = await _service.clone_repository(
            request.repo_url
        )
    except ValueError as exc:
        logger.warning("Git clone validation failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        )
    except Exception as exc:
        logger.exception("Git clone failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clone repository: {exc}",
        )

    return SourceIngestionResponse(
        project_id=res.project_id,
        project_path=res.project_path,
        message="Git repository cloned successfully.",
        detected_framework=getattr(res, "detected_framework", None),
        stats=getattr(res, "stats", None),
        metrics=getattr(res, "metrics", None),
    )
