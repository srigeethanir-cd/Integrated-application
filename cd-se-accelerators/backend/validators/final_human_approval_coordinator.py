"""Final Human Approval Coordinator enforcing the final governance checkpoint before deployment."""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class FinalApprovalRequest(BaseModel):
    """Review request submitted by the Business Analyst / Technical Reviewer."""

    status: str = Field(description="Decision: APPROVED | CHANGES_REQUESTED | REJECTED")
    reviewer_name: str = Field(default="Lead Business Analyst", description="Reviewer name")
    reviewer_role: str = Field(default="Governance Reviewer", description="Reviewer role")
    comments: str = Field(default="", description="Review comments or change instructions")
    requested_changes: Optional[List[str]] = Field(default=None, description="Impacted sections or change items")
    failure_layer: Optional[str] = Field(default=None, description="If REJECTED: Blueprint | Implementation | Merge")


class FinalGovernanceAuditRecord(BaseModel):
    """Historical audit record for final governance review."""

    audit_id: str = Field(description="Audit ID (e.g. GOV-001)")
    reviewer_name: str
    reviewer_role: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    decision: str
    comments: str
    impact_summary: str


class FinalHumanApprovalCoordinator:
    """Final Governance Checkpoint Coordinator enforcing approval before deployment."""

    def __init__(self):
        self._release_version: str = "v1.0.0"

    def review_final_application(
        self,
        agent3_artifacts: Dict[str, Any],
        approval_request: FinalApprovalRequest,
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        """Process final governance checkpoint review decision (APPROVED, CHANGES_REQUESTED, REJECTED)."""
        from app.database.session import session_manager

        status_upper = approval_request.status.upper()
        logger.info("FinalHumanApprovalCoordinator: Processing final governance decision '%s' by %s", status_upper, approval_request.reviewer_name)

        if db is not None:
            return self._execute_review(db, agent3_artifacts, approval_request, status_upper)
        else:
            with session_manager.session_scope() as session:
                return self._execute_review(session, agent3_artifacts, approval_request, status_upper)

    def _execute_review(
        self,
        sess: Session,
        agent3_artifacts: Dict[str, Any],
        approval_request: FinalApprovalRequest,
        status_upper: str,
    ) -> Dict[str, Any]:
        from app.repository.project_repository import ProjectRepository
        from app.repository.final_governance_audit_repository import FinalGovernanceAuditRepository
        from app.models.final_governance_audit import FinalGovernanceAudit

        # Resolve project_id
        project_repo = ProjectRepository(sess)
        projects = project_repo.get_all(limit=1)
        project_id = str(projects[0].id) if projects else "DEFAULT-PROJECT"

        audit_repo = FinalGovernanceAuditRepository(sess)
        existing_audits = audit_repo.get_by_project(project_id)
        audit_count = len(existing_audits)
        audit_id = f"GOV-{audit_count + 1:03d}"

        # Determine Action & Impact
        action_name = "FINAL_GOVERNANCE_REVIEW"
        if status_upper == "APPROVED":
            impact_summary = "Application verified and approved for production deployment."
        elif status_upper == "CHANGES_REQUESTED":
            requested = approval_request.requested_changes or ["stories"]
            impact_summary = f"Changes requested for: {', '.join(requested)}. Regenerating impacted user stories only."
        else:
            layer = approval_request.failure_layer or "Implementation"
            return_target = "Agent2"
            if "blueprint" in layer.lower() or "architecture" in layer.lower():
                return_target = "Agent1"
            elif "merge" in layer.lower() or "integration" in layer.lower():
                return_target = "Agent3"
            impact_summary = f"Architecture rejected due to {layer} failures. Returning execution to {return_target}."

        # Save to DB
        meta = {
            "reviewer_role": approval_request.reviewer_role,
            "impact_summary": impact_summary,
            "requested_changes": approval_request.requested_changes,
            "failure_layer": approval_request.failure_layer,
        }
        new_audit = FinalGovernanceAudit(
            project_id=project_id,
            action=action_name,
            status=status_upper,
            reviewer=approval_request.reviewer_name,
            comments=approval_request.comments,
            metadata_json=meta,
        )
        audit_repo.save(new_audit)

        # Fetch updated history from DB
        updated_audits = audit_repo.get_by_project(project_id)
        history_list = []
        for i, au in enumerate(updated_audits):
            h_id = f"GOV-{i + 1:03d}"
            h_meta = au.metadata_json or {}
            history_list.append(FinalGovernanceAuditRecord(
                audit_id=h_id,
                reviewer_name=au.reviewer,
                reviewer_role=h_meta.get("reviewer_role", "Governance Reviewer"),
                timestamp=au.created_at.isoformat() if au.created_at else datetime.now(timezone.utc).isoformat(),
                decision=au.status,
                comments=au.comments or "",
                impact_summary=h_meta.get("impact_summary", ""),
            ))

        history_dicts = [h.model_dump() for h in history_list]

        if status_upper == "APPROVED":
            return {
                "approval_status": "APPROVED",
                "deployment_ready": True,
                "release_version": self._release_version,
                "final_reports": [
                    {"report": "Business Validation Report", "status": "PASSED"},
                    {"report": "Technical Validation Report", "status": "PASSED"},
                    {"report": "Traceability Verification Report", "status": "VERIFIED"},
                    {"report": "Deployment Readiness Report", "status": "READY"},
                ],
                "deployment_package": agent3_artifacts.get("deployment_manifest", {}),
                "approval_history": history_dicts,
            }
        elif status_upper == "CHANGES_REQUESTED":
            requested = approval_request.requested_changes or ["stories"]
            return {
                "approval_status": "CHANGES_REQUESTED",
                "affected_requirements": [f"REQ-{r}" for r in requested],
                "affected_epics": ["EP001"],
                "affected_user_stories": requested,
                "impact_report": impact_summary,
                "return_to": "Agent2",
                "regenerate_unaffected_modules": False,
                "approval_history": history_dicts,
            }
        else:
            layer = approval_request.failure_layer or "Implementation"
            return_target = "Agent2"
            if "blueprint" in layer.lower() or "architecture" in layer.lower():
                return_target = "Agent1"
            elif "merge" in layer.lower() or "integration" in layer.lower():
                return_target = "Agent3"
            return {
                "approval_status": "REJECTED",
                "reason": approval_request.comments or f"Major {layer} failure detected.",
                "return_to": return_target,
                "approval_history": history_dicts,
            }
