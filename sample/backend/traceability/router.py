"""FastAPI Traceability Router exposing REST endpoints for matrix, impact analysis, and log dashboards."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.responses import success_response
from traceability.traceability_service import TraceabilityService

router = APIRouter(prefix="/traceability", tags=["Traceability System"])

# Singleton traceability service instance
traceability_service = TraceabilityService()


def get_traceability_service() -> TraceabilityService:
    """Dependency providing singleton TraceabilityService instance."""
    return traceability_service


class ImpactAnalysisRequest(BaseModel):
    """Payload to request change impact analysis for a target node."""

    target_node_key: str = Field(description="Target node key (e.g. US101, REQ-US101, /api/v1/users)")


@router.get("/matrix", response_model=Dict[str, Any])
def get_traceability_matrix(
    service: TraceabilityService = Depends(get_traceability_service),
) -> Any:
    """Retrieve full 9-layer traceability matrix nodes and directional links."""
    summary = service.get_full_matrix()
    return success_response(
        data=summary,
        message="Traceability matrix retrieved successfully.",
    )


@router.post("/impact-analysis", response_model=Dict[str, Any])
def analyze_change_impact(
    req: ImpactAnalysisRequest,
    service: TraceabilityService = Depends(get_traceability_service),
) -> Any:
    """Perform change impact analysis for a target architectural node."""
    report = service.analyze_change_impact(req.target_node_key)
    return success_response(
        data=report.model_dump(),
        message=f"Impact analysis completed for '{req.target_node_key}'.",
    )


@router.get("/dashboard", response_model=Dict[str, Any])
def get_log_dashboard(
    service: TraceabilityService = Depends(get_traceability_service),
) -> Any:
    """Retrieve log dashboard string and matrix coverage metrics."""
    dashboard_text = service.render_log_dashboard()
    summary = service.get_full_matrix()
    return success_response(
        data={
            "dashboard_ascii": dashboard_text,
            "matrix_summary": summary,
        },
        message="Traceability log dashboard retrieved successfully.",
    )
