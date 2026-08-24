"""FastAPI Workflow Router exposing REST endpoints for LangGraph orchestration."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from fastapi import APIRouter, Depends, HTTPException, status

from app.approval import ApprovalReviewRequest
from app.core.responses import success_response
from langgraph.workflow import WorkflowOrchestrator

router = APIRouter(prefix="/workflow", tags=["LangGraph Workflow Engine"])

# Singleton workflow orchestrator
workflow_orchestrator = WorkflowOrchestrator()


def get_workflow_orchestrator() -> WorkflowOrchestrator:
    """Dependency providing singleton WorkflowOrchestrator instance."""
    return workflow_orchestrator


class StartWorkflowRequest(BaseModel):
    """Payload to launch a new LangGraph workflow run."""

    project_name: str = Field(default="AI_BA_Accelerated_App", description="Target application name")
    tech_stack: str = Field(default="Python FastAPI / React TypeScript", description="Tech stack description")
    user_stories: List[Dict[str, Any]] = Field(description="Raw user stories")
    image_path: Optional[str] = Field(default=None, description="Path to wireframe image")


class HumanApprovalSubmission(BaseModel):
    """Payload to submit human BA approval decision."""

    execution_id: str = Field(description="Workflow execution run ID")
    review_request: ApprovalReviewRequest = Field(description="Approval review decision")


@router.post("/start", response_model=Dict[str, Any])
def start_workflow(
    req: StartWorkflowRequest,
    orchestrator: WorkflowOrchestrator = Depends(get_workflow_orchestrator),
) -> Any:
    """Start a new end-to-end LangGraph workflow orchestration run."""
    state = orchestrator.start_workflow(
        user_stories=req.user_stories,
        project_name=req.project_name,
        tech_stack=req.tech_stack,
        image_path=req.image_path,
    )
    return success_response(
        data=state,
        message=f"Workflow execution {state['execution_id']} started. Status: {state['workflow_status']}",
    )


@router.get("/status/{execution_id}", response_model=Dict[str, Any])
def get_workflow_status(
    execution_id: str,
    orchestrator: WorkflowOrchestrator = Depends(get_workflow_orchestrator),
) -> Any:
    """Get the current execution state and status for a workflow run."""
    state = orchestrator.get_workflow_status(execution_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Execution ID '{execution_id}' not found.")
    return success_response(
        data=state,
    )


@router.post("/approval", response_model=Dict[str, Any])
def submit_human_approval(
    req: HumanApprovalSubmission,
    orchestrator: WorkflowOrchestrator = Depends(get_workflow_orchestrator),
) -> Any:
    """Submit human BA approval decision to resume/refine a paused workflow run."""
    try:
        updated_state = orchestrator.submit_human_approval(
            execution_id=req.execution_id,
            req=req.review_request,
        )
        return success_response(
            data=updated_state,
            message=f"Approval action submitted. Workflow status: {updated_state['workflow_status']}",
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/resume/{execution_id}", response_model=Dict[str, Any])
def resume_workflow(
    execution_id: str,
    orchestrator: WorkflowOrchestrator = Depends(get_workflow_orchestrator),
) -> Any:
    """Resume execution for a paused workflow run."""
    try:
        updated_state = orchestrator.resume_workflow(execution_id)
        return success_response(
            data=updated_state,
            message=f"Workflow execution {execution_id} resumed.",
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
