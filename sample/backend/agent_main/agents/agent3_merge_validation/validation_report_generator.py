"""Validation Report Generator — Formats and persists system validation reports."""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ValidationReportGenerator:
    """Generates structured ValidationReport.json and audit summaries."""

    def __init__(self) -> None:
        self.logger = logger

    def generate_report(
        self,
        integrated_project_root: str,
        validation_results: Dict[str, Any],
        repair_attempts: int = 0,
    ) -> Dict[str, Any]:
        """Generate and save ValidationReport.json into integrated project root."""
        out_dir = Path(integrated_project_root)
        out_dir.mkdir(parents=True, exist_ok=True)

        report = {
            "report_type": "SYSTEM_VALIDATION",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "overall_status": validation_results.get("status", "PASS"),
            "repair_attempts": repair_attempts,
            "checks": validation_results.get("checks", {}),
            "errors": validation_results.get("errors", []),
            "summary": {
                "total_checks": len(validation_results.get("checks", {})),
                "passed": validation_results.get("status") == "PASS",
            },
        }

        report_file = out_dir / "ValidationReport.json"
        try:
            with open(report_file, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2)
            self.logger.info("Validation report written to %s", report_file)
        except Exception as e:
            self.logger.warning("Failed to write validation report: %s", e)

        return report
