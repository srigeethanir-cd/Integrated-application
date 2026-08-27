"""
API routes for Test Case Generation – Module 7.

Translates Strategy and Edge Case plans into TestCasePlanResponse.
"""

import logging
from fastapi import APIRouter, HTTPException, status

from app.models.strategy_models import StrategyPlanResponse
from app.models.test_case_models import TestCasePlanResponse
from app.services.test_case_generator.test_case_generator import TestCaseGeneratorService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/test_case", tags=["Test Case Generator"])

_service = TestCaseGeneratorService()


@router.post(
    "/generate",
    response_model=TestCasePlanResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate TestCase Plan",
    description="Accept validated StrategyPlanResponse directly as request body "
                "to generate structured, framework-agnostic execution test cases.",
)
async def generate_test_cases(
    request: StrategyPlanResponse,
) -> TestCasePlanResponse:
    """Generate structured test cases directly from strategy plan."""
    try:
        return _service.generate_test_cases(request)
    except ValueError as exc:
        logger.warning("Test Case validation error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        )
    except Exception as exc:
        logger.exception("Test Case generation failed unexpectedly")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Test Case generation failed: {exc}",
        )
