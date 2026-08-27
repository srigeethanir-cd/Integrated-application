"""Accelerator State definition for LangGraph workflow orchestration."""

from typing import Any, Dict, List, Optional, TypedDict
from pydantic import BaseModel, Field


class AcceleratorStateDict(TypedDict, total=False):
    """LangGraph TypedDict state dictionary."""

    execution_id: str
    project_name: str
    tech_stack: str
    image_path: Optional[str]
    user_stories: List[Dict[str, Any]]
    agent0_output: Optional[Dict[str, Any]]
    agent1_output: Optional[Dict[str, Any]]
    approval_status: str
    approval_feedback: Optional[str]
    impacted_sections: Optional[List[str]]
    agent2_output: Optional[Dict[str, Any]]
    agent3_output: Optional[Dict[str, Any]]
    retry_count: int
    current_node: str
    error_logs: List[str]
    traceability_matrix: Dict[str, Any]
    workflow_status: str


class AcceleratorStateModel(BaseModel):
    """Pydantic model representation of AcceleratorState."""

    execution_id: str = Field(description="Unique execution run ID")
    project_name: str = Field(default="AI_BA_Accelerated_App", description="Target application name")
    tech_stack: str = Field(default="Python FastAPI / React TypeScript", description="Tech stack description")
    image_path: Optional[str] = Field(default=None, description="Path to wireframe image")
    user_stories: List[Dict[str, Any]] = Field(default_factory=list, description="Raw user stories")
    agent0_output: Optional[Dict[str, Any]] = Field(default=None, description="Agent 0 output")
    agent1_output: Optional[Dict[str, Any]] = Field(default=None, description="Agent 1 output")
    approval_status: str = Field(default="PENDING", description="Approval status: PENDING | APPROVED | CHANGES_REQUESTED | REJECTED")
    approval_feedback: Optional[str] = Field(default=None, description="BA review feedback")
    impacted_sections: Optional[List[str]] = Field(default=None, description="Impacted sections for regeneration")
    agent2_output: Optional[Dict[str, Any]] = Field(default=None, description="Agent 2 story outputs")
    agent3_output: Optional[Dict[str, Any]] = Field(default=None, description="Agent 3 integration output")
    retry_count: int = Field(default=0, description="Current node retry count")
    current_node: str = Field(default="START", description="Active workflow node name")
    error_logs: List[str] = Field(default_factory=list, description="Execution error logs")
    traceability_matrix: Dict[str, Any] = Field(default_factory=dict, description="Global traceability matrix")
    workflow_status: str = Field(default="RUNNING", description="Workflow state: RUNNING | PAUSED_FOR_APPROVAL | COMPLETED | FAILED")
