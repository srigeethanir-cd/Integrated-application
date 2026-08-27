"""
API routes for Framework Detection (Module 2).

Business logic lives in ``FrameworkDetectorService``; this handler only
translates the HTTP layer.
"""

import logging

from fastapi import APIRouter, HTTPException, status

from app.models.framework_models import (
    FrameworkDetectRequest,
    FrameworkDetectResponse,
)
from app.services.framework_detection.framework_detector_service import (
    FrameworkDetectorService,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/framework", tags=["Framework Detection"])

# Service instance – in a larger app this would come from a DI container.
_service = FrameworkDetectorService()


@router.post(
    "/detect",
    response_model=FrameworkDetectResponse,
    status_code=status.HTTP_200_OK,
    summary="Detect frontend framework",
    description="Analyse a project directory or ZIP archive and detect the frontend "
    "framework in use (React, Angular, Next.js, or Unknown).",
)
async def detect_framework(
    request: FrameworkDetectRequest,
) -> FrameworkDetectResponse:
    """Detect the frontend framework used by a project directory or ZIP archive."""
    try:
        result = _service.detect(request.project_path)
    except FileNotFoundError as exc:
        logger.warning("Framework detection path not found: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        )
    except ValueError as exc:
        logger.warning("Framework detection validation failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        )
    except Exception as exc:
        logger.exception("Framework detection failed unexpectedly")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Framework detection failed: {exc}",
        )

    return FrameworkDetectResponse(**result)
