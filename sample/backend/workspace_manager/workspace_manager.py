"""Workspace Manager — Isolated Story Workspace Lifecycle.

Manages the isolated workspace lifecycle for user stories:
- Create Story Workspace
- Resolve Story Workspace Path
- Clean Story Workspace
- Delete Story Workspace
- Archive Story Workspace
- Return Story Workspace Manifest
"""

import os
import shutil
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

REQUIRED_SUBDIRS = ["backend", "frontend", "database", "metadata", "validation", "logs"]


class WorkspaceManager:
    """Manages creation, resolution, cleaning, deletion, and archiving of story workspaces."""

    def __init__(self, base_workspace_dir: Optional[str] = None) -> None:
        self.base_workspace_dir = base_workspace_dir

    def resolve_story_workspace(self, project_root: str, story_id: str) -> str:
        """Resolve the absolute path for a story's isolated workspace.

        Args:
            project_root: Path to the project root directory.
            story_id: Identifier for the user story (e.g., "US001").

        Returns:
            Absolute path to outputs/projects/<project>/workspace/<story_id>
        """
        clean_story_id = story_id.replace("-", "").replace("_", "").upper()
        if not clean_story_id.startswith("US") and story_id.isalnum():
            clean_story_id = f"US{story_id}"
        elif not story_id.isalnum():
            clean_story_id = story_id

        workspace_dir = os.path.join(project_root, "workspace", clean_story_id)
        return os.path.abspath(workspace_dir)

    def create_story_workspace(self, project_root: str, story_id: str) -> str:
        """Create an isolated workspace directory structure for a user story.

        Structure:
            workspace/<story_id>/
                ├── backend/
                ├── frontend/
                ├── database/
                ├── metadata/
                ├── validation/
                └── logs/

        Args:
            project_root: Path to the project root directory.
            story_id: Story identifier (e.g. "US001").

        Returns:
            Path to the created story workspace directory.
        """
        story_ws_path = self.resolve_story_workspace(project_root, story_id)
        os.makedirs(story_ws_path, exist_ok=True)

        for subdir in REQUIRED_SUBDIRS:
            sub_path = os.path.join(story_ws_path, subdir)
            os.makedirs(sub_path, exist_ok=True)

        logger.info("Created isolated story workspace at: %s", story_ws_path)
        return story_ws_path

    def clean_story_workspace(self, project_root: str, story_id: str) -> None:
        """Clean all files inside a story workspace without deleting root folders."""
        story_ws_path = self.resolve_story_workspace(project_root, story_id)
        if not os.path.exists(story_ws_path):
            return

        for root, dirs, files in os.walk(story_ws_path, topdown=False):
            for f in files:
                os.remove(os.path.join(root, f))
            for d in dirs:
                if d not in REQUIRED_SUBDIRS or os.path.dirname(os.path.join(root, d)) != story_ws_path:
                    shutil.rmtree(os.path.join(root, d), ignore_errors=True)

        logger.info("Cleaned story workspace at: %s", story_ws_path)

    def delete_story_workspace(self, project_root: str, story_id: str) -> bool:
        """Delete an isolated story workspace entirely (used on validation failure).

        Args:
            project_root: Path to project root directory.
            story_id: User story identifier.

        Returns:
            True if workspace was deleted, False if it did not exist.
        """
        story_ws_path = self.resolve_story_workspace(project_root, story_id)
        if os.path.exists(story_ws_path):
            shutil.rmtree(story_ws_path, ignore_errors=True)
            logger.info("Deleted isolated story workspace at: %s", story_ws_path)
            return True
        return False

    def archive_story_workspace(self, project_root: str, story_id: str) -> str:
        """Archive a story workspace after successful merge.

        Args:
            project_root: Path to project root directory.
            story_id: User story identifier.

        Returns:
            Path to the archived location.
        """
        story_ws_path = self.resolve_story_workspace(project_root, story_id)
        if not os.path.exists(story_ws_path):
            raise FileNotFoundError(f"Story workspace does not exist: {story_ws_path}")

        archive_dir = os.path.join(project_root, "workspace", ".archive")
        os.makedirs(archive_dir, exist_ok=True)
        archive_path = os.path.join(archive_dir, os.path.basename(story_ws_path))

        if os.path.exists(archive_path):
            shutil.rmtree(archive_path, ignore_errors=True)

        shutil.move(story_ws_path, archive_path)
        logger.info("Archived story workspace to: %s", archive_path)
        return archive_path

    def return_story_workspace(self, project_root: str, story_id: str) -> Dict[str, Any]:
        """Return a complete manifest of all files present in a story workspace.

        Args:
            project_root: Path to project root directory.
            story_id: User story identifier.

        Returns:
            Dictionary with workspace metadata and list of relative file paths.
        """
        story_ws_path = self.resolve_story_workspace(project_root, story_id)
        if not os.path.exists(story_ws_path):
            return {"story_id": story_id, "exists": False, "files": []}

        files_list: List[str] = []
        for root, _, files in os.walk(story_ws_path):
            for f in files:
                abs_f = os.path.join(root, f)
                rel_f = os.path.relpath(abs_f, story_ws_path)
                files_list.append(rel_f)

        return {
            "story_id": story_id,
            "exists": True,
            "workspace_path": story_ws_path,
            "files": sorted(files_list),
            "file_count": len(files_list),
        }
