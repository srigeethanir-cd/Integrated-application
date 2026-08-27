"""File Service Client — Client interface for story workspace file operations."""

import logging
from typing import Any, Dict, List, Optional
# pyrefly: ignore [missing-import]
from workspace_manager.file_writer import FileWriter

logger = logging.getLogger(__name__)


class FileServiceClient:
    """Client for writing story artifacts strictly into isolated story workspace."""

    def __init__(self, story_workspace_path: Optional[str] = None) -> None:
        self.writer = FileWriter(workspace_path=story_workspace_path)

    def save_artifacts(
        self, artifacts: Dict[str, str], story_workspace_path: Optional[str] = None
    ) -> List[str]:
        """Save story generated artifacts to workspace.

        Args:
            artifacts: Dict mapping relative_path -> code_content.
            story_workspace_path: Story workspace directory path.

        Returns:
            List of written file paths.
        """
        return self.writer.write_batch(artifacts, story_workspace_path=story_workspace_path)
