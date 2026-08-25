"""Download endpoints for generated TestForge artifacts."""

from __future__ import annotations

import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from fastapi.background import BackgroundTasks
from fastapi.responses import FileResponse

from app.dependencies.export import (
    CodeUnderstandingServiceDependency,
    ProjectRepositoryDependency,
    PytestExportServiceDependency,
)
from app.services.export import (
    ExportArtifactError,
    ExportCreationError,
    ExportValidationError,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/projects", tags=["exports"])


def _remove_archive(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except OSError:
        logger.warning("Unable to clean temporary export archive path=%s", path)


@router.get(
    "/{project_id}/exports/test-suite",
    response_class=FileResponse,
    summary="Export a production-ready pytest suite",
    responses={
        404: {"description": "Project or generated tests not found"},
        409: {"description": "Generated artifacts are incomplete or corrupted"},
        500: {"description": "The ZIP archive could not be created"},
    },
)
def export_test_suite(
    project_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    projects: ProjectRepositoryDependency,
    understanding: CodeUnderstandingServiceDependency,
    exporter: PytestExportServiceDependency,
) -> FileResponse:
    project = projects.get_by_id(project_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "project_not_found", "message": "Project not found"},
        )
    state = understanding.get_latest_pipeline_state(project_id)
    try:
        archive = exporter.create_archive(
            project_name=project.name,
            pipeline_state=state,
        )
    except ExportValidationError as error:
        code = "corrupted_export_artifact" if isinstance(error, ExportArtifactError) else "export_not_ready"
        status_code = status.HTTP_409_CONFLICT if isinstance(error, ExportArtifactError) else status.HTTP_404_NOT_FOUND
        raise HTTPException(
            status_code=status_code,
            detail={"code": code, "message": str(error)},
        ) from error
    except ExportCreationError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "export_creation_failed", "message": str(error)},
        ) from error
    background_tasks.add_task(_remove_archive, archive)
    return FileResponse(
        path=archive,
        media_type="application/zip",
        filename="test-suite.zip",
        background=background_tasks,
    )
