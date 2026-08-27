"""File Writer — Story Workspace File Writer.

Ensures that code artifacts generated during story processing are written
EXCLUSIVELY into the story's isolated workspace (workspace/<story_id>/).
"""

import os
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class FileWriter:
    """Writes code generation artifacts strictly into the isolated story workspace."""

    def __init__(self, workspace_path: Optional[str] = None) -> None:
        self.workspace_path = workspace_path

    def write_file(self, target_path: str, content: str, story_workspace_path: Optional[str] = None) -> str:
        """Write code content to a file inside the story workspace.

        Args:
            target_path: Relative path within the story workspace (e.g. "backend/main.py").
            content: File body content.
            story_workspace_path: Path to story workspace root. If None, uses self.workspace_path.

        Returns:
            Absolute path to written file.
        """
        base_dir = story_workspace_path or self.workspace_path
        if not base_dir:
            raise ValueError("Story workspace path must be specified.")

        # Ensure target_path is relative to base_dir
        clean_path = target_path.lstrip("/\\")
        abs_path = os.path.abspath(os.path.join(base_dir, clean_path))

        # Security check: ensure path stays within story workspace
        real_base = os.path.realpath(base_dir)
        real_target = os.path.realpath(abs_path)
        if not real_target.startswith(real_base):
            raise ValueError(f"Target path '{target_path}' escapes story workspace directory '{base_dir}'.")

        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info("Wrote artifact to story workspace: %s", abs_path)
        return abs_path

    def write_batch(
        self, files: Dict[str, str], story_workspace_path: Optional[str] = None
    ) -> List[str]:
        """Write a dictionary of relative_path -> content to story workspace.

        Args:
            files: Dict mapping relative file path to file content string.
            story_workspace_path: Path to story workspace root.

        Returns:
            List of absolute written file paths.
        """
        written = []
        for rel_path, content in files.items():
            path = self.write_file(rel_path, content, story_workspace_path=story_workspace_path)
            written.append(path)
        return written
