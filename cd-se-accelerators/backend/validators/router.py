"""FastAPI Router for Modular Validation Framework and Final Governance Coordinator."""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.responses import success_response
from validators.final_human_approval_coordinator import FinalApprovalRequest, FinalHumanApprovalCoordinator
from validators.validation_framework import ValidationFramework

router = APIRouter(tags=["Modular Validation & Final Governance"])

# Singletons
validation_framework = ValidationFramework()
final_coordinator = FinalHumanApprovalCoordinator()


def get_validation_framework() -> ValidationFramework:
    """Dependency providing singleton ValidationFramework instance."""
    return validation_framework


def get_final_coordinator() -> FinalHumanApprovalCoordinator:
    """Dependency providing singleton FinalHumanApprovalCoordinator instance."""
    return final_coordinator


class RunValidatorsRequest(BaseModel):
    """Payload to trigger modular validation suite."""

    project_root: str = Field(default="./integrated_project", description="Target integrated project path")
    master_blueprint: Optional[Dict[str, Any]] = Field(default=None, description="Optional MasterBlueprint dict")


@router.post("/validators/run-all", response_model=Dict[str, Any])
def run_all_validators(
    req: RunValidatorsRequest,
    framework: ValidationFramework = Depends(get_validation_framework),
) -> Any:
    """Run all 10 independent modular validators on project root."""
    report = framework.run_all_validators(
        project_root=req.project_root,
        master_blueprint=req.master_blueprint,
    )
    return success_response(
        data=report.model_dump(),
        message=f"Validation completed. Passed {report.passed_count}/{report.total_validators} validators.",
    )


@router.post("/approval/final/decision", response_model=Dict[str, Any])
def submit_final_governance_decision(
    req: FinalApprovalRequest,
    coordinator: FinalHumanApprovalCoordinator = Depends(get_final_coordinator),
) -> Any:
    """Submit final governance checkpoint approval decision (APPROVED | CHANGES_REQUESTED | REJECTED)."""
    mock_agent3_artifacts = {
        "deployment_manifest": {
            "app_name": "AI_BA_Accelerated_App",
            "version": "1.0.0",
            "deployment_status": "READY_FOR_PRODUCTION",
        }
    }
    result = coordinator.review_final_application(
        agent3_artifacts=mock_agent3_artifacts,
        approval_request=req,
    )
    return success_response(
        data=result,
        message=f"Final governance decision '{req.status}' processed successfully.",
    )
