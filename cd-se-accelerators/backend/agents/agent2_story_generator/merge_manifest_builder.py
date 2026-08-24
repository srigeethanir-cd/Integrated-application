"""Merge Manifest Builder for Agent 2.

Compares generated story workspace files against the Integrated Project Skeleton to build MergeManifest.json for Agent 3.
"""

import os
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class MergeAction(BaseModel):
    """Specification of an integration action for Agent 3."""

    action_type: str = Field(description="Action: CREATE | MODIFY | CONFLICT")
    source_file: str = Field(description="Relative path inside story workspace")
    target_file: str = Field(description="Target path in Integrated Project")
    conflict_risk: str = Field(default="NONE", description="Risk level: NONE | LOW | HIGH")


class MergeManifestBuilder:
    """Builds MergeManifest.json describing required integration actions for Agent 3."""

    def build_manifest(
        self,
        story_key: str,
        epic_key: str,
        story_workspace_path: str,
        project_skeleton_root: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Compare story workspace files against project skeleton and generate merge manifest."""
        actions: List[MergeAction] = []
        story_root = Path(story_workspace_path)
        skeleton_root = Path(project_skeleton_root) if project_skeleton_root else None

        for root, _, files in os.walk(story_root):
            for file in files:
                if file in ("story.json", "traceability.json", "MergeManifest.json", "StoryValidationReport.json"):
                    continue

                abs_source = Path(root) / file
                rel_source = os.path.relpath(abs_source, story_root)

                # Determine action type
                action_type = "CREATE"
                conflict_risk = "NONE"

                if skeleton_root:
                    target_path = skeleton_root / rel_source
                    if target_path.exists():
                        action_type = "MODIFY"
                        conflict_risk = "LOW"

                actions.append(
                    MergeAction(
                        action_type=action_type,
                        source_file=rel_source,
                        target_file=rel_source,
                        conflict_risk=conflict_risk,
                    )
                )

        manifest = {
            "story_key": story_key,
            "epic_key": epic_key,
            "source_workspace": story_workspace_path,
            "total_actions": len(actions),
            "create_count": sum(1 for a in actions if a.action_type == "CREATE"),
            "modify_count": sum(1 for a in actions if a.action_type == "MODIFY"),
            "conflict_count": sum(1 for a in actions if a.action_type == "CONFLICT"),
            "actions": [a.model_dump() for a in actions],
        }

        # Save manifest inside story workspace
        manifest_path = story_root / "MergeManifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            import json
            json.dump(manifest, f, indent=2)

        logger.info("MergeManifestBuilder: Generated MergeManifest.json for story %s (%d actions)", story_key, len(actions))
        return manifest
