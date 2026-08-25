"""
API routes for Intermediate Representation (IR) Generation – Module 4.

Business logic lives in ``IRGeneratorService``; this route only handles HTTP concerns.
"""

import logging
from fastapi import APIRouter, HTTPException, status

from app.models.analyzer_models import AnalyzerResponse
from app.models.ir_models import FrameworkAgnosticIR
from app.services.ir_generator.ir_generator_service import IRGeneratorService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ir", tags=["IR Generator"])

_service = IRGeneratorService()


@router.post(
    "/generate",
    response_model=FrameworkAgnosticIR,
    status_code=status.HTTP_200_OK,
    summary="Generate Framework-Agnostic IR",
    description="Accept validated parser output from Module 3 (AnalyzerResponse) "
                "and convert it into a common, normalized framework-agnostic IR.",
)
async def generate_ir(
    analyzer_output: AnalyzerResponse,
) -> FrameworkAgnosticIR:
    """Generate normalized IR from Module 3 output."""
    try:
        return _service.generate_ir(analyzer_output)
    except ValueError as exc:
        logger.warning("IR generation validation error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        )
    except Exception as exc:
        logger.exception("IR generation failed unexpectedly")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"IR generation failed: {exc}",
        )
