"""Merge Manager — High-level coordinator for workspace story merges."""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from agents.agent3_merge_validation.merge_engine import MergeEngine
from agents.agent3_merge_validation.shared_promoter import SharedPromoter
from agents.agent3_merge_validation.merge_report_generator import MergeReportGenerator

logger = logging.getLogger(__name__)


class MergeManager:
    """Coordinates merge execution between individual story sandboxes and integrated project root."""

    def __init__(self) -> None:
        self.merge_engine = MergeEngine()
        self.shared_promoter = SharedPromoter()
        self.report_generator = MergeReportGenerator()

    def merge_all_stories(
        self,
        workspace_root: str,
        integrated_project_root: str,
        approved_only: bool = True,
    ) -> Dict[str, Any]:
        """Execute complete merge pass across all story directories."""
        logger.info("MergeManager: Initiating story merge from %s to %s", workspace_root, integrated_project_root)

        # 1. Promote shared modules
        promoted = self.shared_promoter.promote_shared_modules(
            workspace_root=workspace_root,
            integrated_project_root=integrated_project_root,
        )

        # 2. Merge story artifacts
        merge_results = self.merge_engine.merge_all_stories(
            workspace_root=workspace_root,
            integrated_project_root=integrated_project_root,
            approved_only=approved_only,
        )

        return {
            "promoted_modules": promoted,
            "merge_results": merge_results,
            "status": "COMPLETED",
        }
