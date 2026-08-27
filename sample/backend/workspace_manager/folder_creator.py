"""Folder Creator for Workspace Manager.

Scaffolds isolated project workspace structures (epics, core, metadata, versions, integrated_project).
"""

import logging
from pathlib import Path
from typing import Dict, List

logger = logging.getLogger(__name__)


class FolderCreator:
    """Scaffolds directory structures for isolated project workspaces."""

    DEFAULT_WORKSPACE_FOLDERS = [
        "epics",
        "core/auth",
        "core/middleware",
        "core/utils",
        "core/models",
        "core/hooks",
        "metadata",
        "versions",
        "validation",
        "preview",
        "ui_visualization",
        "traceability",
        "logs",
        "integrated_project/backend/app/api",
        "integrated_project/backend/app/services",
        "integrated_project/backend/app/models",
        "integrated_project/backend/app/database",
        "integrated_project/frontend/src",
        "integrated_project/docs",
    ]

    def create_workspace_folders(self, workspace_root: str) -> List[str]:
        """Create all required workspace directories under workspace_root."""
        root = Path(workspace_root)
        created_paths: List[str] = []

        for folder in self.DEFAULT_WORKSPACE_FOLDERS:
            folder_path = root / folder
            folder_path.mkdir(parents=True, exist_ok=True)
            created_paths.append(str(folder_path))

        logger.info("FolderCreator: Scaffolded %d workspace directories under %s", len(created_paths), workspace_root)
        return created_paths

    def create_story_folders(self, workspace_root: str, epic_key: str, story_key: str) -> Dict[str, str]:
        """Create isolated story workspace folders (workspace/epics/EPxxx/USxxx/)."""
        story_root = Path(workspace_root) / "epics" / epic_key / story_key
        subfolders = ["backend", "frontend", "database", "tests", "ui_visualization"]
        paths = {"story_root": str(story_root)}

        story_root.mkdir(parents=True, exist_ok=True)
        for sub in subfolders:
            sub_path = story_root / sub
            sub_path.mkdir(parents=True, exist_ok=True)
            paths[sub] = str(sub_path)

        return paths
