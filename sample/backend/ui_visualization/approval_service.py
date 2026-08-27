import os
import json
import uuid
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from app.database.session import SessionLocal
from app.models.story import Story as StoryModel
from app.models import StoryApproval, StoryAudit

logger = logging.getLogger(__name__)

class ApprovalService:
    """Manages Human Approval Gateways and Automatic Error Recovery."""

    def __init__(self, workspace_root: str = "workspace"):
        self.workspace_root = Path(workspace_root)

    def analyze_rejection_root_cause(self, comments: str, errors: List[str]) -> Dict[str, str]:
        """Analyzes comments/errors to detect the root cause and assign the responsible agent."""
        text_to_search = (comments + " " + " ".join(errors)).lower()

        if any(w in text_to_search for w in ["ui", "css", "styling", "layout", "visual", "frontend", "wireframe", "screenshot"]):
            return {
                "cause": "UI/Visual layout mismatch with wireframe spec",
                "responsible_agent": "Agent0"
            }
        elif any(w in text_to_search for w in ["blueprint", "epic", "architecture", "contract", "spec", "missing blueprint"]):
            return {
                "cause": "Missing blueprint configuration or architectural contract",
                "responsible_agent": "Agent1"
            }
        elif any(w in text_to_search for w in ["validation", "lint", "complexity", "naming standards", "brackets"]):
            return {
                "cause": "Coding standards check or syntactic validation failed",
                "responsible_agent": "Validation Engine"
            }
        elif any(w in text_to_search for w in ["merge", "conflict", "collision", "duplicate route"]):
            return {
                "cause": "Integration route collision or AST merge conflict",
                "responsible_agent": "Merge Engine"
            }
        else:
            # Default to backend story developer
            return {
                "cause": "Backend logic / API router or unit test implementation issue",
                "responsible_agent": "Agent2"
            }

    def record_story_review(
        self,
        story_id: str,
        decision: str, # APPROVED, REJECTED, CHANGES_REQUESTED
        comments: str,
        reviewer: str = "Business Analyst"
    ) -> Dict[str, Any]:
        """Applies a review status to a story, triggering recovery if rejected."""
        db = SessionLocal()
        try:
            story_uuid = uuid.UUID(story_id) if isinstance(story_id, str) else story_id
            story_db = db.query(StoryModel).filter(StoryModel.story_id == story_uuid).first()
            if not story_db:
                raise ValueError(f"Story with ID {story_id} not found.")

            # Record review decision
            approval = StoryApproval(
                story_id=story_uuid,
                reviewer=reviewer,
                comments=comments,
                decision=decision,
                version=story_db.version
            )
            db.add(approval)

            # Record state transition audit
            prev_status = story_db.approval_status
            story_db.approval_status = decision.upper()
            
            audit = StoryAudit(
                story_id=story_uuid,
                user=reviewer,
                agent="Orchestrator",
                previous_state=prev_status,
                new_state=decision.upper(),
                comments=comments
            )
            db.add(audit)

            recovery_info = {}
            if decision.upper() in ("REJECTED", "CHANGES_REQUESTED"):
                # Run automatic error recovery analysis
                val_errors = []
                # Fetch validation errors from latest report
                latest_val = sorted(story_db.validations, key=lambda x: x.created_at)[-1] if story_db.validations else None
                if latest_val and isinstance(latest_val.report, dict):
                    val_errors = latest_val.report.get("errors", [])

                recovery_info = self.analyze_rejection_root_cause(comments, val_errors)
                logger.info(
                    "Automatic Error Recovery: Story %s rejected. Root Cause: %s. Routing back to: %s",
                    story_db.story_key, recovery_info["cause"], recovery_info["responsible_agent"]
                )

            db.commit()

            # Write recovery report inside story workspace
            if recovery_info:
                story_folder = self.workspace_root / str(story_db.project_id) / "epics" / str(story_db.epic.epic_key if story_db.epic else "EP001").upper() / str(story_db.story_key).upper()
                story_folder.mkdir(parents=True, exist_ok=True)
                recovery_file = story_folder / "ui_visualization" / "recovery_analysis.json"
                recovery_file.parent.mkdir(parents=True, exist_ok=True)
                with open(recovery_file, "w", encoding="utf-8") as f:
                    json.dump({
                        "rejected_at": datetime.now(timezone.utc).isoformat(),
                        "comments": comments,
                        "root_cause": recovery_info["cause"],
                        "responsible_agent": recovery_info["responsible_agent"],
                        "action": f"Routing user story back to {recovery_info['responsible_agent']} for targeted regeneration."
                    }, f, indent=2)

            return {
                "story_key": story_db.story_key,
                "decision": decision.upper(),
                "recovery": recovery_info
            }
        except Exception as e:
            db.rollback()
            logger.error("Failed to record story review: %s", e)
            raise
        finally:
            db.close()

    def set_project_approval(self, project_id: str, approved: bool, comments: str) -> Dict[str, Any]:
        """Sets project-level approval state inside a local file within the project workspace."""
        proj_folder = self.workspace_root / project_id
        proj_folder.mkdir(parents=True, exist_ok=True)
        
        approval_file = proj_folder / "project_approval.json"
        status_str = "APPROVED" if approved else "REJECTED"
        
        approval_data = {
            "project_id": project_id,
            "approved": approved,
            "status": status_str,
            "comments": comments,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        with open(approval_file, "w", encoding="utf-8") as f:
            json.dump(approval_data, f, indent=2)
            
        logger.info("Project Approval Gate: Project %s set to %s. Comments: %s", project_id, status_str, comments)
        return approval_data

    def is_project_approved(self, project_id: str) -> bool:
        """Query if the project has been approved at the project-level gate."""
        approval_file = self.workspace_root / project_id / "project_approval.json"
        if not approval_file.exists():
            return False
        try:
            with open(approval_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("status") == "APPROVED"
        except Exception:
            return False
