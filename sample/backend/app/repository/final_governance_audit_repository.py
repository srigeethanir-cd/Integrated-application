from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.final_governance_audit import FinalGovernanceAudit
from app.repository.base_repository import BaseRepository


class FinalGovernanceAuditRepository(BaseRepository[FinalGovernanceAudit]):
    """Data-access layer for final governance audits."""

    def __init__(self, db: Session) -> None:
        super().__init__(FinalGovernanceAudit, db)

    def get_by_project(self, project_id: str) -> list[FinalGovernanceAudit]:
        """Look up all final governance audits for a given project ID."""
        stmt = (
            select(FinalGovernanceAudit)
            .where(FinalGovernanceAudit.project_id == project_id)
            .order_by(FinalGovernanceAudit.created_at.asc())
        )
        return list(self.db.scalars(stmt).all())

    def get_all_audits(self) -> list[FinalGovernanceAudit]:
        """Get all audits ordered by creation time."""
        stmt = select(FinalGovernanceAudit).order_by(FinalGovernanceAudit.created_at.asc())
        return list(self.db.scalars(stmt).all())
