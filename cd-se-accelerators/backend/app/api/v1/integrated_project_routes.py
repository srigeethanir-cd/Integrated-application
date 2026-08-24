"""REST API endpoints for managing integrated project application lifecycle and runtime."""

import logging
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, status

from app.core.responses import success_response
from integrated_runner.process_manager import get_runner

router = APIRouter(prefix="/integrated-project", tags=["Integrated Project Runner"])
logger = logging.getLogger(__name__)


class StartProjectRequest(BaseModel):
    project_path: Optional[str] = Field(default=None, description="Optional custom root directory for integrated application")


@router.post("/start", response_model=Dict[str, Any])
def start_integrated_project(req: Optional[StartProjectRequest] = None) -> Any:
    """Start or retrieve running status of the merged integrated application."""
    runner = get_runner()
    path = req.project_path if req else None
    result = runner.start_application(project_path=path)
    return success_response(
        data=result,
        message=result["message"]
    )


@router.post("/stop", response_model=Dict[str, Any])
def stop_integrated_project() -> Any:
    """Gracefully stop integrated application server processes."""
    runner = get_runner()
    result = runner.stop_application()
    return success_response(
        data=result,
        message="Integrated application server processes terminated."
    )


@router.get("/status", response_model=Dict[str, Any])
def get_integrated_project_status() -> Any:
    """Get current running status, health, ports, and URLs of the integrated application."""
    runner = get_runner()
    return success_response(
        data=runner.get_runtime_status(),
        message="Runtime status retrieved successfully."
    )


@router.get("/runtime", response_model=Dict[str, Any])
def get_integrated_project_runtime() -> Any:
    """Get active runtime URLs and port configuration."""
    runner = get_runner()
    return success_response(
        data=runner.get_runtime_status(),
        message="Runtime configuration retrieved."
    )


@router.get("/logs", response_model=Dict[str, Any])
def get_integrated_project_logs(limit: int = 100) -> Any:
    """Fetch startup and execution logs from server stdout/stderr streams."""
    runner = get_runner()
    return success_response(
        data={
            "logs": runner.get_logs(limit=limit),
            "status": runner.status_state,
            "is_healthy": runner.is_healthy() if runner.status_state == "running" else False
        },
        message="Logs retrieved successfully."
    )


@router.get("/health", response_model=Dict[str, Any])
def get_integrated_project_health() -> Any:
    """Perform direct HTTP health probe of running frontend and backend servers."""
    runner = get_runner()
    is_healthy = runner.is_healthy()
    return success_response(
        data={
            "healthy": is_healthy,
            "status": runner.status_state,
            "frontend_url": f"http://localhost:{runner.frontend_port}",
            "backend_url": f"http://localhost:{runner.backend_port}"
        },
        message="Health probe completed."
    )
