"""
API routes for Test Execution – Module 10.

Provides POST /test_execution/run to execute Jest tests on generated suites.
"""

import logging
from fastapi import APIRouter, HTTPException, status

from app.models.test_execution_models import TestExecutionRequest, TestExecutionReport
from app.services.test_execution.execution_service import TestExecutionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/test_execution", tags=["Test Execution Service"])

_service = TestExecutionService()


@router.post(
    "/run",
    response_model=TestExecutionReport,
    status_code=status.HTTP_200_OK,
    summary="Execute Generated Jest Tests",
    description="Locates the stored test manifest, triggers Jest test execution, collects coverage, and records results.",
)
async def run_test_execution(
    request: TestExecutionRequest,
) -> TestExecutionReport:
    """Run Jest test suite for a given pipeline run ID."""
    try:
        res = _service.execute_pipeline_tests(request.pipeline_run_id)
        return res
    except FileNotFoundError as exc:
        logger.warning("Pipeline run or file not found during execution: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        )
    except ValueError as exc:
        logger.warning("Invalid input or framework configurations: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        )
    except Exception as exc:
        logger.exception("Test execution process encountered unexpected failure")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Test execution failed: {exc}",
        )
