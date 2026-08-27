"""Approval History Tracker storing version audit trails for all approval cycles."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.prompt_template import PromptApproval
from app.approval.approval_schema import ApprovalHistoryRecord
from app.approval.approval_state import ApprovalStatus, ImpactAnalysisResult

logger = logging.getLogger(__name__)


class ApprovalHistoryTracker:
    """Maintains an audit trail of every approval review cycle across blueprint versions in the DB."""

    def record_cycle(
        self,
        blueprint_version: str,
        reviewer: str,
        comments: str,
        status: ApprovalStatus,
        change_summary: str,
        impact_analysis: ImpactAnalysisResult,
        db: Optional[Session] = None,
    ) -> ApprovalHistoryRecord:
        """Record a new approval review cycle in history."""
        from app.database.session import SessionLocal
        sess = db or SessionLocal()
        try:
            # We fetch latest to preserve the bundle_json if any
            latest_stmt = select(PromptApproval).where(PromptApproval.prompt_template_id == "blueprint_approval_gate").order_by(PromptApproval.approved_at.desc())
            latest = sess.scalars(latest_stmt).first()
            bundle = latest.bundle_json if latest else {}

            # Embed history metadata in the bundle_json
            updated_bundle = dict(bundle) if bundle else {}
            updated_bundle["change_summary"] = change_summary
            updated_bundle["impact_analysis"] = impact_analysis.model_dump()

            new_record = PromptApproval(
                prompt_template_id="blueprint_approval_gate",
                reviewer=reviewer,
                decision=status.value,
                comments=comments,
                approved_version=blueprint_version,
                approved_at=datetime.now(timezone.utc),
                bundle_json=updated_bundle
            )
            sess.add(new_record)
            sess.commit()
            sess.refresh(new_record)
            
            # Fetch all history to compute the cycle count
            count_stmt = select(PromptApproval).where(PromptApproval.prompt_template_id == "blueprint_approval_gate")
            count = len(sess.scalars(count_stmt).all())
            
            cycle_id = f"CYCLE-{count:03d}"
            
            record = ApprovalHistoryRecord(
                cycle_id=cycle_id,
                blueprint_version=blueprint_version,
                reviewer=reviewer,
                timestamp=new_record.approved_at.isoformat(),
                comments=comments,
                status=status,
                change_summary=change_summary,
                impact_analysis=impact_analysis,
            )
            return record
        except Exception as e:
            sess.rollback()
            logger.error(f"Failed to record cycle: {e}")
            raise e
        finally:
            if db is None:
                sess.close()

    def get_history(self, db: Optional[Session] = None) -> List[ApprovalHistoryRecord]:
        """Return all historical approval review records."""
        from app.database.session import SessionLocal
        sess = db or SessionLocal()
        try:
            stmt = select(PromptApproval).where(PromptApproval.prompt_template_id == "blueprint_approval_gate").order_by(PromptApproval.approved_at.asc())
            results = sess.scalars(stmt).all()
            history = []
            for idx, r in enumerate(results, start=1):
                bundle = r.bundle_json or {}
                impact_dict = bundle.get("impact_analysis", {})
                impact_res = ImpactAnalysisResult(
                    impacted_sections=impact_dict.get("impacted_sections", []),
                    unaffected_sections=impact_dict.get("unaffected_sections", []),
                    impact_summary=impact_dict.get("impact_summary", "No impact detected")
                )
                history.append(
                    ApprovalHistoryRecord(
                        cycle_id=f"CYCLE-{idx:03d}",
                        blueprint_version=r.approved_version,
                        reviewer=r.reviewer,
                        timestamp=r.approved_at.isoformat() if r.approved_at else datetime.now(timezone.utc).isoformat(),
                        comments=r.comments or "",
                        status=ApprovalStatus(r.decision),
                        change_summary=bundle.get("change_summary", ""),
                        impact_analysis=impact_res,
                    )
                )
            return history
        except Exception as e:
            logger.error(f"Failed to fetch history: {e}")
            return []
        finally:
            if db is None:
                sess.close()

    def get_latest_record(self, db: Optional[Session] = None) -> Optional[ApprovalHistoryRecord]:
        """Return the most recent approval review record."""
        history = self.get_history(db)
        return history[-1] if history else None

