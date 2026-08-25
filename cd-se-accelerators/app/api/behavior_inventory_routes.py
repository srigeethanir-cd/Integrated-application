"""
Behavior Inventory REST API Routes.

Exposes endpoints to retrieve or generate Frontend Behavior Inventory payloads for pipeline runs.
"""

import json
import os
from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.models.behavior_inventory_models import BehaviorInventoryResponse
from app.services.behavior_inventory_service import BehaviorInventoryService
from app.services.pipeline_orchestrator_service import PERSISTENT_RUNS_DIR

router = APIRouter(prefix="/behavior_inventory", tags=["Behavior Inventory"])

_service = BehaviorInventoryService()


class BehaviorInventoryGenerateRequest(BaseModel):
    """Payload to trigger behavior inventory building for an analysis payload."""
    analysis: Dict[str, Any]
    project_name: Optional[str] = "Project"
    project_id: Optional[str] = None
    pipeline_run_id: Optional[str] = None
    framework: Optional[str] = "React"


@router.post("/generate", response_model=BehaviorInventoryResponse, summary="Generate Behavior Inventory")
def generate_behavior_inventory(req: BehaviorInventoryGenerateRequest) -> BehaviorInventoryResponse:
    """Generate structured Frontend Behavior Inventory from raw analysis result data."""
    try:
        return _service.build_inventory(
            analysis_result=req.analysis,
            project_name=req.project_name or "Project",
            project_id=req.project_id,
            pipeline_run_id=req.pipeline_run_id,
            framework=req.framework or "React",
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to generate behavior inventory: {exc}")


@router.get("/{pipeline_run_id}", response_model=BehaviorInventoryResponse, summary="Get Persisted Behavior Inventory")
def get_behavior_inventory(pipeline_run_id: str) -> BehaviorInventoryResponse:
    """Retrieve persisted behavior inventory JSON for a specific pipeline run."""
    run_dir = os.path.join(PERSISTENT_RUNS_DIR, pipeline_run_id)
    inv_file = os.path.join(run_dir, "behavior_inventory.json")

    if not os.path.exists(inv_file):
        raise HTTPException(status_code=404, detail=f"Behavior inventory for pipeline_run_id '{pipeline_run_id}' not found.")

    try:
        with open(inv_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return BehaviorInventoryResponse.model_validate(data)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to parse stored behavior inventory: {exc}")
