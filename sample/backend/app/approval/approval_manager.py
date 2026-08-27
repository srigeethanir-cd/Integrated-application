"""Approval Manager enforcing strict execution gate for Agent 2 and LangGraph workflows."""

import logging
from typing import Any, Dict

from app.approval.approval_service import ApprovalService
from app.approval.approval_state import ApprovalStatus
from app.core.exceptions import ForbiddenError

logger = logging.getLogger(__name__)


class ApprovalManager:
    """Enforces execution gate rule: 'No implementation code should begin before approval'."""

    def __init__(self, approval_service: ApprovalService):
        self.service = approval_service

    def verify_execution_allowed(self) -> bool:
        """Check if execution is allowed to proceed to Agent 2 / LangGraph."""
        status = self.service.get_current_status()
        if status != ApprovalStatus.APPROVED:
            error_msg = f"Execution Blocked: Current approval status is '{status.value}'. Architecture must be APPROVED by Business Analyst before code generation can start."
            logger.warning(error_msg)
            raise ForbiddenError(detail=error_msg)
        return True

    def can_start_implementation(self) -> bool:
        """Boolean status check without raising exception."""
        return self.service.get_current_status() == ApprovalStatus.APPROVED
