"""Metadata Writer — Updates project metadata after story processing."""

import os
import json
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class MetadataWriter:
    """Writes story generation metadata into project and story metadata files."""

    def __init__(self, project_root: Optional[str] = None) -> None:
        self.project_root = project_root

    def update_metadata(
        self,
        story_id: str,
        execution_summary: Dict[str, Any],
        project_root: Optional[str] = None,
        story_workspace_path: Optional[str] = None,
    ) -> str:
        """Write execution metadata to <project_root>/metadata/story_<story_id>.json."""
        root = project_root or self.project_root
        if not root:
            return ""

        metadata_dir = os.path.join(root, "metadata")
        os.makedirs(metadata_dir, exist_ok=True)

        clean_id = story_id.replace("-", "_").lower()
        meta_file = os.path.join(metadata_dir, f"story_{clean_id}.json")

        meta_content = {
            "story_id": story_id,
            "status": execution_summary.get("status", "completed"),
            "merged": execution_summary.get("merged", False),
            "merged_files": execution_summary.get("merged_files", []),
            "timestamp": execution_summary.get("timestamp"),
            "validation": execution_summary.get("validation", {}),
        }

        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(meta_content, f, indent=2)

        # Also save copy inside story workspace if available
        if story_workspace_path and os.path.exists(story_workspace_path):
            ws_meta_dir = os.path.join(story_workspace_path, "metadata")
            os.makedirs(ws_meta_dir, exist_ok=True)
            with open(os.path.join(ws_meta_dir, "story_metadata.json"), "w", encoding="utf-8") as f:
                json.dump(meta_content, f, indent=2)

        logger.info("Updated metadata for story %s at %s", story_id, meta_file)
        return meta_file
