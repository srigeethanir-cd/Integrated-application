"""
API routes for Test Strategy Generation – Module 5.

Business logic lives in ``StrategyEngine``; this route only handles HTTP concerns.
"""

import logging
from fastapi import APIRouter, HTTPException, status

from app.models.ir_models import FrameworkAgnosticIR
from app.models.strategy_models import StrategyPlanResponse
from app.services.test_strategy.strategy_engine_service import StrategyEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/strategy", tags=["Test Strategy Engine"])

_engine = StrategyEngine()


@router.post(
    "/generate",
    response_model=StrategyPlanResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate Test Strategies",
    description="Accept validated FrameworkAgnosticIR from Module 4 "
                "and generate a comprehensive, framework-agnostic list of test strategies.",
)
async def generate_strategies(
    ir: FrameworkAgnosticIR,
) -> StrategyPlanResponse:
    """Generate test strategies from IR."""
    try:
        return _engine.generate_strategies(ir)
    except ValueError as exc:
        logger.warning("Strategy engine validation error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        )
    except Exception as exc:
        logger.exception("Strategy generation failed unexpectedly")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Strategy generation failed: {exc}",
        )
