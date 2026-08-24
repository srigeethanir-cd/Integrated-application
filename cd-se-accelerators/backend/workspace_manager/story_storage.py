"""Story Storage for Workspace Manager.

Manages storage and retrieval of story-specific code, schemas, and metadata inside workspace/epics/EPxxx/USxxx/.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class StoryArtifactRecord(BaseModel):
    """Metadata record of a stored story artifact."""

    story_key: str = Field(description="Story ID (e.g. US001)")
    epic_key: str = Field(description="Epic ID (e.g. EP001)")
    artifact_type: str = Field(description="Artifact type: backend | frontend | database | test | metadata")
    relative_path: str = Field(description="Path relative to story workspace")
    size_bytes: int = Field(description="Artifact size in bytes")


class StoryStorage:
    """Stores and retrieves story-specific artifacts inside isolated workspaces."""

    def save_story_artifact(
        self,
        workspace_root: str,
        epic_key: str,
        story_key: str,
        artifact_type: str,
        filename: str,
        content: str,
    ) -> StoryArtifactRecord:
        """Write a story artifact into workspace/epics/EPxxx/USxxx/<artifact_type>/<filename>."""
        story_dir = Path(workspace_root) / "epics" / epic_key / story_key
        sub_dir = story_dir / artifact_type if artifact_type in ("backend", "frontend", "database", "tests") else story_dir
        sub_dir.mkdir(parents=True, exist_ok=True)

        target_file = sub_dir / filename
        with open(target_file, "w", encoding="utf-8") as f:
            f.write(content)

        rel_path = str(target_file.relative_to(story_dir))
        size = len(content.encode("utf-8"))

        logger.info("StoryStorage: Stored artifact %s (%d bytes)", rel_path, size)
        return StoryArtifactRecord(
            story_key=story_key,
            epic_key=epic_key,
            artifact_type=artifact_type,
            relative_path=rel_path,
            size_bytes=size,
        )

    def load_story_artifact(
        self,
        workspace_root: str,
        epic_key: str,
        story_key: str,
        relative_path: str,
    ) -> Optional[str]:
        """Read a story artifact content string."""
        target_file = Path(workspace_root) / "epics" / epic_key / story_key / relative_path
        if not target_file.exists():
            return None
        with open(target_file, "r", encoding="utf-8") as f:
            return f.read()
