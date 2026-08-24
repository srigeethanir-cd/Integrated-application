"""Structural Comparator for evaluating file diffs between story workspaces and integrated projects."""

import os
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class FileDiffRecord(BaseModel):
    """File difference record."""

    action_type: str = Field(description="Action: CREATE | MODIFY | DELETE | CONFLICT")
    relative_path: str = Field(description="Relative filepath under project root")
    source_path: str = Field(description="Source path inside story workspace")
    target_path: str = Field(description="Target path inside integrated project")
    risk_level: str = Field(default="NONE", description="Risk level: NONE | LOW | HIGH")


class StructuralComparator:
    """Compares story workspace file trees against target integrated project structures."""

    def compare_trees(
        self,
        story_workspace_root: str,
        integrated_project_root: str,
    ) -> List[FileDiffRecord]:
        """Compare story workspace files with target integrated project files."""
        diff_records: List[FileDiffRecord] = []
        src_root = Path(story_workspace_root)
        tgt_root = Path(integrated_project_root)

        if not src_root.exists():
            return diff_records

        for root, _, files in os.walk(src_root):
            for file in files:
                if file in ("story.json", "traceability.json", "MergeManifest.json", "StoryValidationReport.json", "StoryExecutionSummary.json"):
                    continue

                abs_src = Path(root) / file
                rel_path = os.path.relpath(abs_src, src_root)
                abs_tgt = tgt_root / rel_path

                if abs_tgt.exists():
                    action_type = "MODIFY"
                    risk_level = "LOW"
                    # Check if file has conflicting modifications
                    if abs_src.stat().st_size != abs_tgt.stat().st_size:
                        action_type = "CONFLICT"
                        risk_level = "HIGH"
                else:
                    action_type = "CREATE"
                    risk_level = "NONE"

                diff_records.append(
                    FileDiffRecord(
                        action_type=action_type,
                        relative_path=rel_path,
                        source_path=str(abs_src),
                        target_path=str(abs_tgt),
                        risk_level=risk_level,
                    )
                )

        logger.info("StructuralComparator: Compared %s against %s (%d diffs found)", story_workspace_root, integrated_project_root, len(diff_records))
        return diff_records
