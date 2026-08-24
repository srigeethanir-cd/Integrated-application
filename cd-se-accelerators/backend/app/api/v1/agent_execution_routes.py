"""FastAPI Agent Execution Routes for Agent 0 through Agent 3."""

import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, status

from agents.agent0_wireframe import Agent0Wireframe
from agents.agent1_blueprint import Agent1Blueprint
from agents.agent2_story_generator import Agent2StoryGenerator
from agents.agent3_merge_validation import Agent3MergeValidation
from app.core.responses import success_response

router = APIRouter(prefix="/agents", tags=["Agent Execution"])
logger = logging.getLogger(__name__)

# Singletons
agent0 = Agent0Wireframe()
agent1 = Agent1Blueprint()
agent2 = Agent2StoryGenerator()
agent3 = Agent3MergeValidation()


class Agent0RunRequest(BaseModel):
    user_stories: List[Dict[str, Any]]
    image_path: Optional[str] = None


from typing import Any, Dict, List, Optional, Union

class Agent1RunRequest(BaseModel):
    project_name: Optional[str] = Field(default="Employee Management System", description="Project name")
    project_description: Optional[str] = Field(default=None, description="Project description")
    tech_stack: Optional[Union[str, Dict[str, Any]]] = Field(default="Python FastAPI / React TypeScript", description="Selected tech stack")
    user_stories: Optional[List[Dict[str, Any]]] = Field(default=None, description="Uploaded user stories JSON")
    stories: Optional[List[Dict[str, Any]]] = Field(default=None, description="Alternative field for user stories")
    ui_metadata: Optional[Dict[str, Any]] = Field(default=None, description="Agent 0 UI metadata")
    wireframe_images: Optional[List[str]] = Field(default=None, description="Uploaded wireframe images")
    workspace_metadata: Optional[Dict[str, Any]] = Field(default=None, description="Existing workspace metadata")
    project_id: Optional[str] = Field(default="PROJ-EMP-001", description="Project ID")


class Agent2RunRequest(BaseModel):
    story: Dict[str, Any]
    master_blueprint: Optional[Dict[str, Any]] = None
    project_id: Optional[str] = Field(default="PROJ-EMP-001", description="Project ID UUID or name")


class Agent3RunRequest(BaseModel):
    workspace_root: str = "./workspace"
    integrated_project_root: str = "./integrated_project"


@router.post("/agent0/run", response_model=Dict[str, Any])
def run_agent0(req: Agent0RunRequest) -> Any:
    """Execute Agent 0 Wireframe to Frontend Generator directly."""
    res = agent0.run({"stories": req.user_stories, "image_path": req.image_path})
    return success_response(data=res, message="Agent 0 executed successfully.")


@router.post("/agent1/run", response_model=Dict[str, Any])
def run_agent1(req: Agent1RunRequest) -> Any:
    """Execute Agent 1 Blueprint & Scaffolding Generator directly."""
    input_stories = req.user_stories or req.stories or []
    if not input_stories:
        # Fallback default stories if none provided
        input_stories = [
            {
                "story_key": "US101",
                "title": "Employee Login",
                "description": "As an employee, I want to log in securely using my email and password.",
                "epic_key": "EP001",
                "acceptance_criteria": ["Validate email format", "Secure password field input"]
            },
            {
                "story_key": "US102",
                "title": "Member Registration",
                "description": "As a user, I want to register an account with validated credentials.",
                "epic_key": "EP001",
                "acceptance_criteria": ["Validate password confirmation match"]
            }
        ]

    res = agent1.process(
        stories=input_stories,
        tech_stack=req.tech_stack or "Python FastAPI / React TypeScript",
        ui_metadata=req.ui_metadata,
        project_id=req.project_id or "PROJ-EMP-001",
        project_name=req.project_name,
        project_description=req.project_description,
        wireframe_images=req.wireframe_images,
        workspace_metadata=req.workspace_metadata,
    )
    return success_response(data=res, message="Agent 1 executed successfully.")


@router.post("/agent2/run", response_model=Dict[str, Any])
def run_agent2(req: Agent2RunRequest) -> Any:
    """Execute Agent 2 Sandboxed Story Code Generator directly."""
    try:
        res = agent2.process_story(
            story=req.story,
            blueprint=req.master_blueprint,
            project_id=req.project_id
        )
        return success_response(data=res, message="Agent 2 executed story successfully.")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/agent3/run", response_model=Dict[str, Any])
def run_agent3(req: Agent3RunRequest) -> Any:
    """Execute Agent 3 Project Integration & System Validation directly."""
    from pathlib import Path
    from app.core.config import get_settings
    settings = get_settings()

    ws_path = Path(req.workspace_root)
    if not ws_path.is_absolute() and not ws_path.exists():
        candidate = Path(settings.workspace_root)
        if candidate.exists():
            ws_path = candidate
        else:
            base_ws = Path(__file__).resolve().parent.parent.parent.parent / "workspace"
            if base_ws.exists():
                ws_path = base_ws

    int_path = Path(req.integrated_project_root)
    if not int_path.is_absolute():
        base_int = Path(__file__).resolve().parent.parent.parent.parent / "integrated_project"
        int_path = base_int

    int_path.mkdir(parents=True, exist_ok=True)
    res = agent3.run_integration(workspace_root=str(ws_path), integrated_project_root=str(int_path))
    return success_response(data=res, message="Agent 3 executed integration successfully.")
