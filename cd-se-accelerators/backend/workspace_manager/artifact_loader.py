"""Artifact Loader for Workspace Manager.

Loads generated blueprints, story artifacts, code files, and manifests across workspaces.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ArtifactLoader:
    """Loads generated architecture artifacts and story manifests from workspace directories."""

    def load_json_artifact(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Load and parse JSON artifact file."""
        path = Path(file_path)
        if not path.exists():
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error("ArtifactLoader: Failed to parse JSON at %s: %s", file_path, e)
            return None

    def load_all_story_manifests(self, workspace_root: str) -> List[Dict[str, Any]]:
        """Scan workspace/epics/ and load all MergeManifest.json artifacts."""
        manifests = []
        epics_dir = Path(workspace_root) / "epics"

        if not epics_dir.exists():
            return manifests

        for root, _, files in os.walk(epics_dir):
            for file in files:
                if file == "MergeManifest.json":
                    manifest_data = self.load_json_artifact(os.path.join(root, file))
                    if manifest_data:
                        manifests.append(manifest_data)

        return manifests
