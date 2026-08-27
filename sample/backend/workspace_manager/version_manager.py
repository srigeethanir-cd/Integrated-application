"""Version Manager for Workspace Manager.

Maintains version history, snapshotting workspace states (v1.0.0, v1.0.1) and supporting version rollbacks.
"""

import json
import logging
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class WorkspaceVersionRecord(BaseModel):
    """Metadata record of a workspace version snapshot."""

    version: str = Field(description="Version string (e.g. v1.0.0)")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    description: str = Field(description="Version snapshot description")
    snapshot_path: str = Field(description="Relative path to version snapshot directory")


class VersionManager:
    """Snapshots workspace state versions and maintains audit trails."""

    def create_version_snapshot(
        self,
        workspace_root: str,
        version: str,
        description: str = "Automated workspace snapshot",
    ) -> WorkspaceVersionRecord:
        """Create a version snapshot of workspace state under workspace/versions/<version>/."""
        ws_root = Path(workspace_root)
        versions_dir = ws_root / "versions" / version
        versions_dir.mkdir(parents=True, exist_ok=True)

        # Snapshot epics and metadata
        epics_dir = ws_root / "epics"
        if epics_dir.exists():
            shutil.copytree(epics_dir, versions_dir / "epics", dirs_exist_ok=True)

        meta_dir = ws_root / "metadata"
        if meta_dir.exists():
            shutil.copytree(meta_dir, versions_dir / "metadata", dirs_exist_ok=True)

        record = WorkspaceVersionRecord(
            version=version,
            timestamp=datetime.now(timezone.utc).isoformat(),
            description=description,
            snapshot_path=str(versions_dir),
        )

        with open(versions_dir / "VersionRecord.json", "w", encoding="utf-8") as f:
            json.dump(record.model_dump(), f, indent=2)

        logger.info("VersionManager: Created workspace version snapshot '%s'", version)
        return record

    def list_versions(self, workspace_root: str) -> List[WorkspaceVersionRecord]:
        """List all version snapshots in workspace/versions/."""
        versions_dir = Path(workspace_root) / "versions"
        records: List[WorkspaceVersionRecord] = []

        if not versions_dir.exists():
            return records

        for ver_folder in versions_dir.iterdir():
            if ver_folder.is_dir():
                rec_file = ver_folder / "VersionRecord.json"
                if rec_file.exists():
                    try:
                        with open(rec_file, "r", encoding="utf-8") as f:
                            records.append(WorkspaceVersionRecord.model_validate(json.load(f)))
                    except Exception:
                        pass

        return sorted(records, key=lambda r: r.version)
