"""FastAPI Approval Router exposing REST endpoints for BA review, actions, and audit trails."""

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.approval.approval_schema import (
    ApprovalReportResponse,
    ApprovalReviewRequest,
)
from app.approval.approval_service import ApprovalService
from app.approval.approval_state import ApprovalStatus
from app.core.responses import success_response

router = APIRouter(prefix="/approval", tags=["Human Approval Gate"])

# Singleton service instance for runtime API
approval_service = ApprovalService()


def get_approval_service() -> ApprovalService:
    """Dependency providing singleton ApprovalService instance."""
    return approval_service


@router.get("/review", response_model=Dict[str, Any])
def get_artifacts_for_review(
    db: Session = Depends(get_db),
    service: ApprovalService = Depends(get_approval_service),
) -> Any:
    """Present generated architecture artifacts and readiness report for BA review."""
    bundle = service.get_review_bundle(db)
    report = service.generate_report(db)
    return success_response(
        data={
            "artifacts_bundle": bundle,
            "readiness_report": report.model_dump(),
            "current_status": service.get_current_status(db).value,
        }
    )


@router.post("/action", response_model=Dict[str, Any])
def submit_approval_action(
    req: ApprovalReviewRequest,
    db: Session = Depends(get_db),
    service: ApprovalService = Depends(get_approval_service),
) -> Any:
    """Submit BA human review decision (APPROVED | CHANGES_REQUESTED | REJECTED)."""
    result = service.review(req, db)
    return success_response(
        data=result,
        message=f"Approval action '{req.status.value}' processed successfully.",
    )


@router.get("/history", response_model=Dict[str, Any])
def get_approval_history(
    db: Session = Depends(get_db),
    service: ApprovalService = Depends(get_approval_service),
) -> Any:
    """Retrieve complete version history and audit trail of all approval cycles."""
    history = service.history_tracker.get_history(db)
    return success_response(
        data=[h.model_dump() for h in history],
    )


@router.get("/status", response_model=Dict[str, Any])
def get_gate_status(
    db: Session = Depends(get_db),
    service: ApprovalService = Depends(get_approval_service),
) -> Any:
    """Check current gate approval status before starting Agent 2 code generation."""
    current_status = service.get_current_status(db)
    can_proceed = current_status == ApprovalStatus.APPROVED
    return success_response(
        data={
            "status": current_status.value,
            "can_proceed_to_agent2": can_proceed,
        }
    )


@router.get("/report", response_model=Dict[str, Any])
def get_approval_report(
    db: Session = Depends(get_db),
    service: ApprovalService = Depends(get_approval_service),
) -> Any:
    """Return the architectural readiness report for the dashboard.

    Dedicated endpoint so the frontend can fetch it directly without
    unpacking the nested envelope returned by /approval/review.
    """
    report = service.generate_report(db)
    history = service.history_tracker.get_history(db)
    return success_response(
        data={
            "readiness_score": report.readiness_score,
            "status": service.get_current_status(db).value,
            "overall_passed": report.overall_passed,
            "validation_checks": [v.model_dump() for v in report.validation_checks],
            "history": [h.model_dump() for h in history],
        },
        message="Approval report retrieved successfully.",
    )

