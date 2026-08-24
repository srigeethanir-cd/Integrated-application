"""Workspace Builder orchestrator for Workspace Manager.

Creates isolated project workspaces, organizes epics and user stories, stores artifacts, maintains version history, and prepares deployment exports.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from workspace_manager.artifact_exporter import ArtifactExporter, DeploymentBundleSpec
from workspace_manager.artifact_loader import ArtifactLoader
from workspace_manager.folder_creator import FolderCreator
from workspace_manager.story_storage import StoryArtifactRecord, StoryStorage
from workspace_manager.version_manager import VersionManager, WorkspaceVersionRecord

logger = logging.getLogger(__name__)


class WorkspaceBuilder:
    """Core orchestrator for workspace lifecycle, sandboxing, versioning, and deployment export."""

    def __init__(self, workspace_root: str = "./workspace"):
        self.workspace_root = workspace_root
        self.folder_creator = FolderCreator()
        self.story_storage = StoryStorage()
        self.version_manager = VersionManager()
        self.artifact_loader = ArtifactLoader()
        self.artifact_exporter = ArtifactExporter()

    def initialize_workspace(self) -> List[str]:
        """Scaffold isolated project workspace directories."""
        return self.folder_creator.create_workspace_folders(self.workspace_root)

    def prepare_story_workspace(self, epic_key: str, story_key: str) -> Dict[str, str]:
        """Create isolated story workspace folders (workspace/epics/EPxxx/USxxx/)."""
        return self.folder_creator.create_story_folders(self.workspace_root, epic_key, story_key)

    def save_story_artifact(
        self,
        epic_key: str,
        story_key: str,
        artifact_type: str,
        filename: str,
        content: str,
    ) -> StoryArtifactRecord:
        """Store story artifact inside isolated workspace."""
        return self.story_storage.save_story_artifact(
            workspace_root=self.workspace_root,
            epic_key=epic_key,
            story_key=story_key,
            artifact_type=artifact_type,
            filename=filename,
            content=content,
        )

    def create_version(self, version: str, description: str = "Automated snapshot") -> WorkspaceVersionRecord:
        """Snapshot workspace state version."""
        return self.version_manager.create_version_snapshot(
            workspace_root=self.workspace_root,
            version=version,
            description=description,
        )

    def export_deployment(self, integrated_project_root: str, output_dir: str) -> DeploymentBundleSpec:
        """Export integrated project into deployment zip archive."""
        return self.artifact_exporter.export_deployment_bundle(
            integrated_project_root=integrated_project_root,
            output_dir=output_dir,
        )
