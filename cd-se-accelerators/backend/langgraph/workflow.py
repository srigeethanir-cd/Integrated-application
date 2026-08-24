"""Workflow Orchestrator for managing LangGraph pipeline executions, state persistence, and human approvals."""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.approval import ApprovalReviewRequest, ApprovalStatus
from app.approval.approval_router import approval_service
from langgraph.graph import build_accelerator_graph
from langgraph.state import AcceleratorStateDict

from app.database.session import session_manager
from app.repository.workflow_execution_repository import WorkflowExecutionRepository

logger = logging.getLogger(__name__)


class WorkflowOrchestrator:
    """High-level engine managing workflow runs, state persistence, and human-in-the-loop approvals."""

    def __init__(self):
        self.pipeline = build_accelerator_graph()
        self.approval_service = approval_service

    def start_workflow(
        self,
        user_stories: List[Dict[str, Any]],
        project_name: str = "AI_BA_Accelerated_App",
        tech_stack: str = "Python FastAPI / React TypeScript",
        image_path: Optional[str] = None,
    ) -> AcceleratorStateDict:
        """Start a new LangGraph workflow execution run."""
        execution_id = f"EXEC-{uuid.uuid4().hex[:8].upper()}"
        logger.info("WorkflowOrchestrator: Starting new workflow run %s for project %s", execution_id, project_name)

        initial_state: AcceleratorStateDict = {
            "execution_id": execution_id,
            "project_name": project_name,
            "tech_stack": tech_stack,
            "image_path": image_path,
            "user_stories": user_stories,
            "approval_status": "PENDING",
            "retry_count": 0,
            "current_node": "START",
            "error_logs": [],
            "traceability_matrix": {},
            "workflow_status": "RUNNING",
        }

        # Execute first step
        state = self.pipeline.execute_step(initial_state)

        # Save to DB
        with session_manager.session_scope() as db:
            repo = WorkflowExecutionRepository(db)
            repo.create({
                "execution_id": execution_id,
                "project_id": project_name,  # Project name acts as the identifier in LangGraph workflow
                "current_step": state.get("current_node", "START"),
                "status": state.get("workflow_status", "RUNNING"),
                "execution_state": dict(state),
            })

        return state

    def submit_human_approval(
        self,
        execution_id: str,
        req: ApprovalReviewRequest,
    ) -> AcceleratorStateDict:
        """Submit BA review decision to pause/resume or refine the workflow."""
        logger.info("WorkflowOrchestrator: Processing approval action '%s' for run %s", req.status.value, execution_id)
        
        with session_manager.session_scope() as db:
            repo = WorkflowExecutionRepository(db)
            db_record = repo.get_by_execution_id(execution_id)
            if not db_record:
                raise ValueError(f"Execution ID '{execution_id}' not found.")
            
            state = dict(db_record.execution_state or {})

        res = self.approval_service.review(req)

        state["approval_status"] = req.status.value
        state["approval_feedback"] = req.comments
        state["impacted_sections"] = req.impacted_sections

        # Resume execution
        updated_state = self.pipeline.execute_step(state)

        # Save back to DB
        with session_manager.session_scope() as db:
            repo = WorkflowExecutionRepository(db)
            db_record = repo.get_by_execution_id(execution_id)
            if db_record:
                repo.update(db_record, {
                    "current_step": updated_state.get("current_node", "START"),
                    "status": updated_state.get("workflow_status", "RUNNING"),
                    "execution_state": dict(updated_state),
                })

        return updated_state

    def resume_workflow(self, execution_id: str) -> AcceleratorStateDict:
        """Resume execution for an existing workflow run."""
        logger.info("WorkflowOrchestrator: Resuming workflow run %s", execution_id)

        with session_manager.session_scope() as db:
            repo = WorkflowExecutionRepository(db)
            db_record = repo.get_by_execution_id(execution_id)
            if not db_record:
                raise ValueError(f"Execution ID '{execution_id}' not found.")
            
            state = dict(db_record.execution_state or {})

        updated_state = self.pipeline.execute_step(state)

        # Save back to DB
        with session_manager.session_scope() as db:
            repo = WorkflowExecutionRepository(db)
            db_record = repo.get_by_execution_id(execution_id)
            if db_record:
                repo.update(db_record, {
                    "current_step": updated_state.get("current_node", "START"),
                    "status": updated_state.get("workflow_status", "RUNNING"),
                    "execution_state": dict(updated_state),
                })

        return updated_state

    def get_workflow_status(self, execution_id: str) -> Optional[AcceleratorStateDict]:
        """Return the current execution state dictionary for execution_id."""
        with session_manager.session_scope() as db:
            repo = WorkflowExecutionRepository(db)
            db_record = repo.get_by_execution_id(execution_id)
            if db_record and db_record.execution_state:
                return dict(db_record.execution_state)
        return None
