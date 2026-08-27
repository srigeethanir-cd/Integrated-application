import os
import logging
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse

from app.core.responses import success_response
from workspace_manager.artifact_exporter import ArtifactExporter

router = APIRouter(prefix="/deployment", tags=["Deployment Packaging"])
logger = logging.getLogger(__name__)

exporter = ArtifactExporter()


class ExportDeploymentRequest(BaseModel):
    integrated_project_root: str = Field(default="./integrated_project", description="Target integrated project path")
    output_dir: str = Field(default="./outputs/exports", description="Export destination directory")
    app_name: str = Field(default="AI_BA_Accelerated_App", description="Application name")
    project_id: Optional[str] = Field(default=None, description="Active Project UUID")


@router.post("/export", response_model=Dict[str, Any])
def export_deployment_package(req: ExportDeploymentRequest) -> Any:
    """Package integrated_project/ into a deployable zip archive and DeploymentManifest.json."""
    bundle = exporter.export_deployment_bundle(
        integrated_project_root=req.integrated_project_root,
        output_dir=req.output_dir,
        app_name=req.app_name,
        project_id=req.project_id,
    )
    return success_response(
        data=bundle.model_dump(),
        message=f"Deployment package exported to '{bundle.archive_path}'.",
    )


@router.get("/download")
def download_deployment_zip(project_id: Optional[str] = Query(None)) -> Any:
    """Directly download the generated deployment ZIP package for a project."""
    bundle = exporter.export_deployment_bundle(
        integrated_project_root=f"./workspace/{project_id}/integrated_project" if project_id else "./integrated_project",
        output_dir="./outputs/exports",
        project_id=project_id,
    )
    return FileResponse(
        path=bundle.archive_path,
        filename=os.path.basename(bundle.archive_path),
        media_type="application/zip",
    )
