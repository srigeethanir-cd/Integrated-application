"""
Frontend Context Extraction Engine (FCE) REST API Routes.

Exposes endpoints to extract or retrieve FrontendContext payloads for pipeline runs.
"""

import json
import os
from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.frontend_context.context_engine import FrontendContextEngine
from app.services.frontend_context.models import FrontendContextResponse
from app.services.pipeline_orchestrator_service import PERSISTENT_RUNS_DIR

router = APIRouter(prefix="/frontend_context", tags=["Frontend Context"])

_engine = FrontendContextEngine()


class FrontendContextExtractRequest(BaseModel):
    """Payload to trigger Frontend Context Extraction Engine."""
    analysis: Dict[str, Any]
    project_path: Optional[str] = None
    project_name: Optional[str] = "Project"
    project_id: Optional[str] = None
    pipeline_run_id: Optional[str] = None
    framework: Optional[str] = "React"


@router.post("/extract", response_model=FrontendContextResponse, summary="Extract Frontend Context")
def extract_frontend_context(req: FrontendContextExtractRequest) -> FrontendContextResponse:
    """Extract structured FrontendContext ground truth from project analysis payload."""
    try:
        return _engine.extract_context(
            analysis_result=req.analysis,
            project_path=req.project_path,
            project_name=req.project_name or "Project",
            project_id=req.project_id,
            pipeline_run_id=req.pipeline_run_id,
            framework=req.framework or "React",
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to extract frontend context: {exc}")


@router.get("/{pipeline_run_id}", response_model=FrontendContextResponse, summary="Get Persisted Frontend Context")
def get_frontend_context(pipeline_run_id: str) -> FrontendContextResponse:
    """Retrieve persisted FrontendContext JSON artifact for a pipeline run."""
    run_dir = os.path.join(PERSISTENT_RUNS_DIR, pipeline_run_id)
    ctx_file = os.path.join(run_dir, "frontend_context.json")

    if not os.path.exists(ctx_file):
        raise HTTPException(status_code=404, detail=f"FrontendContext for pipeline_run_id '{pipeline_run_id}' not found.")

    try:
        with open(ctx_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return FrontendContextResponse.model_validate(data)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to parse stored frontend_context.json: {exc}")
