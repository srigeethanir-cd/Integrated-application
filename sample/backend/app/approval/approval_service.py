"""Approval Service handling BA review actions, impact analysis, and Agent 1 re-invocations."""

import logging
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.approval.approval_history import ApprovalHistoryTracker
from app.approval.approval_report import ApprovalReportGenerator
from app.approval.approval_schema import (
    ApprovalReportResponse,
    ApprovalReviewRequest,
    ArtifactsReviewBundle,
)
from app.approval.approval_state import ApprovalStatus, ImpactAnalysisResult

logger = logging.getLogger(__name__)


class ApprovalService:
    """Core service for managing BA approval reviews, impact analysis, and Agent 1 regeneration payloads."""

    def __init__(self):
        self.report_generator = ApprovalReportGenerator()
        self.history_tracker = ApprovalHistoryTracker()

    def set_artifacts_bundle(self, bundle: Dict[str, Any], db: Optional[Session] = None) -> None:
        """Store generated Agent 1 artifacts bundle for BA review."""
        from app.database.session import SessionLocal
        from app.models.prompt_template import PromptApproval
        from sqlalchemy import select
        from datetime import datetime, timezone
        sess = db or SessionLocal()
        try:
            version = bundle.get("blueprint_version", "1.0.0")
            stmt = select(PromptApproval).where(PromptApproval.prompt_template_id == "blueprint_approval_gate").order_by(PromptApproval.approved_at.desc())
            latest = sess.scalars(stmt).first()
            
            if latest and latest.decision == "PENDING" and latest.approved_version == version:
                latest.bundle_json = bundle
                latest.approved_at = datetime.now(timezone.utc)
            else:
                new_appr = PromptApproval(
                    prompt_template_id="blueprint_approval_gate",
                    reviewer="Business Analyst",
                    decision="PENDING",
                    comments="Pending BA review",
                    approved_version=version,
                    bundle_json=bundle
                )
                sess.add(new_appr)
            sess.commit()
            logger.info("ApprovalService: Set new artifacts bundle for project %s in DB", bundle.get("project_name"))
        except Exception as e:
            sess.rollback()
            logger.error(f"Failed to set artifacts bundle in DB: {e}")
            raise e
        finally:
            if db is None:
                sess.close()

    def get_review_bundle(self, db: Optional[Session] = None) -> Dict[str, Any]:
        """Return the current artifacts bundle for BA review."""
        from app.database.session import SessionLocal
        from app.models.prompt_template import PromptApproval
        from sqlalchemy import select
        sess = db or SessionLocal()
        try:
            stmt = select(PromptApproval).where(PromptApproval.prompt_template_id == "blueprint_approval_gate").order_by(PromptApproval.approved_at.desc())
            latest = sess.scalars(stmt).first()
            if latest and latest.bundle_json:
                return latest.bundle_json
        except Exception as e:
            logger.error(f"Failed to get review bundle from DB: {e}")
        finally:
            if db is None:
                sess.close()
        
        return {
            "project_name": "DefaultApp",
            "blueprint_version": "1.0.0",
            "requirement_json": {},
            "configuration_json": {},
            "generated_frontend": {},
            "master_blueprint": {},
            "folder_structure": [],
            "workspace_manifest": {},
            "dependency_graph": {},
            "api_blueprint": [],
            "database_blueprint": [],
            "traceability_map": {},
        }

    def generate_report(self, db: Optional[Session] = None) -> ApprovalReportResponse:
        """Generate architectural readiness approval report."""
        bundle = self.get_review_bundle(db)
        return self.report_generator.generate_report(bundle)

    def analyze_impact(
        self, comments: str, requested_sections: Optional[List[str]] = None
    ) -> ImpactAnalysisResult:
        """Identify impacted blueprint sections for CHANGES_REQUESTED."""
        all_sections = [
            "api_contracts",
            "database_schemas",
            "frontend_mapping",
            "epics",
            "stories",
            "folder_structure",
        ]

        impacted = requested_sections or []
        if not impacted:
            comments_lower = comments.lower()
            if "api" in comments_lower or "endpoint" in comments_lower:
                impacted.append("api_contracts")
            if "db" in comments_lower or "database" in comments_lower or "table" in comments_lower:
                impacted.append("database_schemas")
            if "frontend" in comments_lower or "ui" in comments_lower:
                impacted.append("frontend_mapping")
            if not impacted:
                impacted = ["stories"]

        unaffected = [s for s in all_sections if s not in impacted]
        summary = f"Impacted sections: {', '.join(impacted)}. Unaffected sections ({', '.join(unaffected)}) will NOT be regenerated."

        return ImpactAnalysisResult(
            impacted_sections=impacted,
            unaffected_sections=unaffected,
            impact_summary=summary,
        )

    def review(self, req: ApprovalReviewRequest, db: Optional[Session] = None) -> Dict[str, Any]:
        """Process human BA review decision (APPROVED, CHANGES_REQUESTED, REJECTED)."""
        logger.info("ApprovalService.review() — Status: %s, Reviewer: %s", req.status.value, req.reviewer)
        from app.database.session import SessionLocal
        from app.models.prompt_template import PromptApproval
        from sqlalchemy import select
        
        sess = db or SessionLocal()
        try:
            stmt = select(PromptApproval).where(PromptApproval.prompt_template_id == "blueprint_approval_gate").order_by(PromptApproval.approved_at.desc())
            latest = sess.scalars(stmt).first()
            
            blueprint_version = "1.0.0"
            if latest:
                blueprint_version = latest.approved_version

            impact_res = ImpactAnalysisResult()
            change_summary = ""

            if req.status == ApprovalStatus.APPROVED:
                current_status = ApprovalStatus.APPROVED
                change_summary = "Architecture approved without modifications. Implementation unlocked."
                logger.info("Architecture APPROVED by BA %s. Implementation code allowed to start.", req.reviewer)

            elif req.status == ApprovalStatus.CHANGES_REQUESTED:
                current_status = ApprovalStatus.CHANGES_REQUESTED
                impact_res = self.analyze_impact(req.comments, req.impacted_sections)
                change_summary = f"Changes requested for: {', '.join(impact_res.impacted_sections)}"
                # Increment version sub-patch
                ver_parts = blueprint_version.split(".")
                blueprint_version = f"{ver_parts[0]}.{ver_parts[1]}.{int(ver_parts[2]) + 1}"
                logger.info("CHANGES_REQUESTED. Returning impacted sections %s to Agent 1.", impact_res.impacted_sections)

            elif req.status == ApprovalStatus.REJECTED:
                current_status = ApprovalStatus.REJECTED
                impact_res = ImpactAnalysisResult(
                    impacted_sections=["ALL_SECTIONS"],
                    unaffected_sections=[],
                    impact_summary="Complete architecture rejected. Returning full blueprint to Agent 1 for complete regeneration.",
                )
                change_summary = "Complete architecture rejected by BA. Full regeneration required."
                ver_parts = blueprint_version.split(".")
                blueprint_version = f"{int(ver_parts[0]) + 1}.0.0"
                logger.warning("Architecture REJECTED by BA. Resetting complete architecture for Agent 1.")

            # Record cycle in audit history
            record = self.history_tracker.record_cycle(
                blueprint_version=blueprint_version,
                reviewer=req.reviewer,
                comments=req.comments,
                status=req.status,
                change_summary=change_summary,
                impact_analysis=impact_res,
                db=sess,
            )

            return {
                "success": True,
                "current_status": current_status.value,
                "blueprint_version": blueprint_version,
                "audit_record": record.model_dump(),
                "agent1_reinvocation_payload": {
                    "impacted_sections_only": impact_res.impacted_sections,
                    "unaffected_sections": impact_res.unaffected_sections,
                    "feedback": req.comments,
                    "full_regeneration": req.status == ApprovalStatus.REJECTED,
                },
            }
        finally:
            if db is None:
                sess.close()

    def get_current_status(self, db: Optional[Session] = None) -> ApprovalStatus:
        """Return current gate approval status."""
        from app.database.session import SessionLocal
        from app.models.prompt_template import PromptApproval
        from sqlalchemy import select
        sess = db or SessionLocal()
        try:
            stmt = select(PromptApproval).where(PromptApproval.prompt_template_id == "blueprint_approval_gate").order_by(PromptApproval.approved_at.desc())
            latest = sess.scalars(stmt).first()
            if latest:
                return ApprovalStatus(latest.decision)
        except Exception as e:
            logger.error(f"Failed to get current status from DB: {e}")
        finally:
            if db is None:
                sess.close()
        return ApprovalStatus.PENDING

