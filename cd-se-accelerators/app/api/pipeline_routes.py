"""
API routes for Development Pipeline Orchestrator.

Provides POST /pipeline/run for executing the full or partial backend testing pipeline.
"""

import logging
from fastapi import APIRouter, HTTPException, status

from app.models.pipeline_models import PipelineRunRequest, PipelineRunResponse
from app.services.pipeline_orchestrator_service import PipelineOrchestratorService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pipeline", tags=["Development Pipeline Orchestrator"])

_service = PipelineOrchestratorService()


@router.post(
    "/run",
    response_model=PipelineRunResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute Pipeline End-to-End (Development & Swagger Testing)",
    description="Orchestrates full or partial backend testing pipeline execution. "
                "Calls all module services in order directly without HTTP overhead. "
                "Supports partial execution via 'run_until', timing toggling via 'include_timings', "
                "and intermediate output filtering via 'include_intermediate_outputs'.",
)
async def run_pipeline(
    request: PipelineRunRequest,
) -> PipelineRunResponse:
    """Run full or partial backend testing pipeline."""
    try:
        res = await _service.run_pipeline(request)
        if res.status == "failed":
            logger.warning("Pipeline orchestrator execution failed at stage '%s': %s", res.failed_stage, res.error_message)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "failed",
                    "failed_stage": res.failed_stage,
                    "error_message": res.error_message,
                    "traceback": res.traceback,
                    "completed_stages": res.completed_stages,
                    "stage_execution_times_ms": res.stage_execution_times_ms,
                    "total_execution_time_ms": res.total_execution_time_ms,
                }
            )
        return res
    except HTTPException:
        raise
    except ValueError as exc:
        logger.warning("Pipeline request validation error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        )
    except Exception as exc:
        logger.exception("Pipeline orchestrator failed unexpectedly")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pipeline execution failed: {exc}",
        )
