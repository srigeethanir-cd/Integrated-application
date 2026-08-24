"""Approval Report Generator calculating readiness scores and issue summaries."""

import logging
from typing import Any, Dict, List

from app.approval.approval_schema import ApprovalReportResponse, ValidationResultItem
from app.approval.blueprint_validator import BlueprintValidator

logger = logging.getLogger(__name__)


class ApprovalReportGenerator:
    """Generates detailed architecture readiness approval reports."""

    def __init__(self):
        self.validator = BlueprintValidator()

    def generate_report(self, bundle: Dict[str, Any]) -> ApprovalReportResponse:
        """Generate architectural readiness approval report."""
        validation_checks = self.validator.validate_all(bundle)

        passed_count = sum(1 for c in validation_checks if c.passed)
        total_count = len(validation_checks)
        readiness_score = round((passed_count / total_count) * 100.0, 1) if total_count > 0 else 0.0
        overall_passed = passed_count == total_count

        master_bp = bundle.get("master_blueprint", {})
        ws_manifest = bundle.get("workspace_manifest", {})

        summary = {
            "epics_count": len(ws_manifest.get("epics", [])),
            "stories_count": len(ws_manifest.get("stories", [])),
            "api_contracts_count": len(master_bp.get("api_contracts", [])),
            "database_tables_count": len(master_bp.get("database_schemas", [])),
            "passed_checks": passed_count,
            "total_checks": total_count,
        }

        return ApprovalReportResponse(
            project_name=bundle.get("project_name", "AI_BA_Accelerated_App"),
            blueprint_version=bundle.get("blueprint_version", "1.0.0"),
            readiness_score=readiness_score,
            validation_checks=validation_checks,
            overall_passed=overall_passed,
            summary=summary,
        )
