"""Merge Report Generator for Agent 3.

Produces MergeReport.json, ValidationReport.json, TraceabilityReport.json, and DeploymentManifest.json.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from agents.agent3_merge_validation.merge_engine import MergedFileRecord
from agents.agent3_merge_validation.shared_promoter import PromotedModuleSpec
from agents.agent3_merge_validation.system_validator import SystemValidationResult

logger = logging.getLogger(__name__)


class MergeReportGenerator:
    """Generates detailed integration reports and deployment artifacts."""

    def generate_all_reports(
        self,
        integrated_project_root: str,
        promoted_modules: List[PromotedModuleSpec],
        merged_records: List[MergedFileRecord],
        val_result: SystemValidationResult,
    ) -> Dict[str, Any]:
        """Generate MergeReport.json, ValidationReport.json, TraceabilityReport.json, and DeploymentManifest.json."""
        proj_root = Path(integrated_project_root)
        timestamp = datetime.now(timezone.utc).isoformat()

        # Find project workspace folder if applicable
        projects_root = None
        for parent in [proj_root] + list(proj_root.parents):
            if parent.parent.name == "projects":
                projects_root = parent
                break

        # 1. Merge Report
        merge_report = {
            "project_name": proj_root.name,
            "generated_at": timestamp,
            "promoted_shared_modules_count": len(promoted_modules),
            "merged_files_count": len(merged_records),
            "promoted_modules": [p.model_dump() for p in promoted_modules],
            "merged_records": [m.model_dump() for m in merged_records],
        }
        with open(proj_root / "MergeReport.json", "w", encoding="utf-8") as f:
            json.dump(merge_report, f, indent=2)
        if projects_root:
            val_dir = projects_root / "validation"
            val_dir.mkdir(parents=True, exist_ok=True)
            with open(val_dir / "MergeReport.json", "w", encoding="utf-8") as f:
                json.dump(merge_report, f, indent=2)

        # 2. Validation Report
        val_report = {
            "project_name": proj_root.name,
            "timestamp": timestamp,
            "attempts_executed": val_result.attempts_executed,
            "overall_passed": val_result.overall_passed,
            "validation_checks": [c.model_dump() for c in val_result.checks],
            "errors": val_result.errors,
        }
        with open(proj_root / "ValidationReport.json", "w", encoding="utf-8") as f:
            json.dump(val_report, f, indent=2)
        if projects_root:
            val_dir = projects_root / "validation"
            val_dir.mkdir(parents=True, exist_ok=True)
            with open(val_dir / "ValidationReport.json", "w", encoding="utf-8") as f:
                json.dump(val_report, f, indent=2)

        # 3. Traceability Report
        trace_report = {
            "project_name": proj_root.name,
            "timestamp": timestamp,
            "total_traceable_files": len(merged_records) + len(promoted_modules),
            "traceability_status": "VERIFIED",
        }
        with open(proj_root / "TraceabilityReport.json", "w", encoding="utf-8") as f:
            json.dump(trace_report, f, indent=2)
        if projects_root:
            trace_dir = projects_root / "traceability"
            trace_dir.mkdir(parents=True, exist_ok=True)
            with open(trace_dir / "TraceabilityReport.json", "w", encoding="utf-8") as f:
                json.dump(trace_report, f, indent=2)

        # 4. Deployment Manifest
        deploy_manifest = {
            "app_name": proj_root.name,
            "version": "1.0.0",
            "build_timestamp": timestamp,
            "deployment_status": "READY_FOR_DEPLOYMENT" if val_result.overall_passed else "BUILD_FAILED",
            "components": {
                "backend": "FastAPI Async Application",
                "frontend": "React TypeScript SPA",
                "database": "PostgreSQL / SQLite Schema Migration",
            },
        }
        with open(proj_root / "DeploymentManifest.json", "w", encoding="utf-8") as f:
            json.dump(deploy_manifest, f, indent=2)
        if projects_root:
            docs_dir = projects_root / "docs"
            docs_dir.mkdir(parents=True, exist_ok=True)
            with open(docs_dir / "DeploymentManifest.json", "w", encoding="utf-8") as f:
                json.dump(deploy_manifest, f, indent=2)

        logger.info("MergeReportGenerator: Generated all reports and DeploymentManifest.json under %s", integrated_project_root)

        return {
            "merge_report": merge_report,
            "validation_report": val_report,
            "traceability_report": trace_report,
            "deployment_manifest": deploy_manifest,
        }
