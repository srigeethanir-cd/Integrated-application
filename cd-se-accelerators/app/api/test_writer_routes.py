"""
API routes for Test Writer – Module 8.

Accepts TestCasePlanResponse and outputs React/Angular code files and manifests.
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status

from app.models.test_case_models import TestCasePlanResponse
from app.models.test_writer_models import TestWriterResponse
from app.services.test_writer.test_writer_service import TestWriterService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/test_writer", tags=["Test Writer"])

_service = TestWriterService()


@router.post(
    "/generate",
    response_model=TestWriterResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate Framework Executable Test Files",
    description="Accept TestCasePlanResponse directly as request body "
                "to output formatted React (Jest+RTL) or Angular (Jest+TestBed) test suites.",
)
async def generate_test_files(
    request: TestCasePlanResponse,
    output_workspace_dir: Optional[str] = Query(None, description="Optional target workspace folder to write output test files and manifest.")
) -> TestWriterResponse:
    """Generate framework-specific test suites and test_manifest.json directly from TestCasePlanResponse."""
    try:
        target_dir = output_workspace_dir or "."
        res = _service.generate_test_suite(request, target_dir)
        if not res.validation_passed:
            logger.warning("Code generation syntax validation check failed: %s", res.validation_errors)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Syntax validation failed on generated test files: {res.validation_errors}"
            )
        return res
    except HTTPException:
        raise
    except ValueError as exc:
        logger.warning("Test case plan validation error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        )
    except Exception as exc:
        logger.exception("Test writer execution failed unexpectedly")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Test Writer execution failed: {exc}",
        )
