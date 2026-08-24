from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.workflow_execution import WorkflowExecutionSession
from app.repository.base_repository import BaseRepository


class WorkflowExecutionRepository(BaseRepository[WorkflowExecutionSession]):
    """Data-access layer for workflow execution sessions."""

    def __init__(self, db: Session) -> None:
        super().__init__(WorkflowExecutionSession, db)

    def get_by_project(self, project_id: str) -> WorkflowExecutionSession | None:
        """Look up a workflow execution session by its project ID."""
        stmt = select(WorkflowExecutionSession).where(WorkflowExecutionSession.project_id == project_id)
        return self.db.scalars(stmt).first()

    def get_by_execution_id(self, execution_id: str) -> WorkflowExecutionSession | None:
        """Look up a workflow execution session by its execution ID."""
        stmt = select(WorkflowExecutionSession).where(WorkflowExecutionSession.execution_id == execution_id)
        return self.db.scalars(stmt).first()
