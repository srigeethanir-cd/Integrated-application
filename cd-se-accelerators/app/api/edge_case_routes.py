"""
API routes for Edge Case Scenario Generation – Module 6.

Business logic lives in ``EdgeCaseGeneratorService``; this route only handles HTTP concerns.
"""

import logging
from typing import Union
from fastapi import APIRouter, HTTPException, status

from app.models.strategy_models import StrategyPlanResponse
from app.models.edge_case_models import EdgeCasePlanRequest, EdgeCasePlanResponse
from app.services.edge_case_generator.edge_case_generator import EdgeCaseGeneratorService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/edge_case", tags=["Edge Case Generator"])

_service = EdgeCaseGeneratorService()


@router.post(
    "/generate",
    response_model=EdgeCasePlanResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate Edge Cases",
    description="Accept validated StrategyPlanResponse and optional IR from Module 5 & 4 "
                "and generate a framework-agnostic collection of edge case scenarios.",
)
async def generate_edge_cases(
    payload: Union[EdgeCasePlanRequest, StrategyPlanResponse],
) -> EdgeCasePlanResponse:
    """Generate edge cases from test strategy plan and optional IR."""
    try:
        return _service.generate_edge_cases(payload)
    except ValueError as exc:
        logger.warning("Edge case validation error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        )
    except Exception as exc:
        logger.exception("Edge case generation failed unexpectedly")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Edge case generation failed: {exc}",
        )
