"""
API routes for Project Analyzer & Parser (Module 3).

Single endpoint – all business logic is in ``ProjectAnalyzerService``.
This handler only translates HTTP concerns.
"""

import logging

from fastapi import APIRouter, HTTPException, status

from app.models.analyzer_models import AnalyzerRequest, AnalyzerResponse
from app.services.project_analyzer.project_analyzer_service import (
    ProjectAnalyzerService,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analyzer", tags=["Project Analyzer"])

# Service instance – in a larger app this would come from a DI container.
_service = ProjectAnalyzerService()


@router.post(
    "/analyze",
    response_model=AnalyzerResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyse a project",
    description=(
        "Auto-detect the frontend framework in the given project directory "
        "and parse all source files to extract structured information "
        "(components, props, hooks, services, templates, etc.). "
        "The framework is detected automatically — do not supply it."
    ),
)
async def analyze_project(
    request: AnalyzerRequest,
) -> AnalyzerResponse:
    """Analyse a project: detect framework, parse, return structured data."""
    try:
        result = _service.analyze(request.project_path)
    except FileNotFoundError as exc:
        logger.warning("Analyzer path not found: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        )
    except ValueError as exc:
        logger.warning("Analyzer validation error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        )
    except RuntimeError as exc:
        logger.exception("Analyzer runtime error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )
    except Exception as exc:
        logger.exception("Analyzer failed unexpectedly")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Project analysis failed: {exc}",
        )

    return result
