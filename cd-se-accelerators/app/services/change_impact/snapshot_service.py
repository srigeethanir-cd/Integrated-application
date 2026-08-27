import hashlib
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.db.models import ProjectSnapshot, FileSnapshot

logger = logging.getLogger(__name__)


class SnapshotService:
    """Computes content-based SHA-256 snapshots of project workspaces."""

    def __init__(self, db: Optional[Session] = None) -> None:
        self.db = db

    def _get_session(self) -> Session:
        return self.db if self.db is not None else SessionLocal()

    def _compute_sha256(self, file_path: str) -> str:
        """Compute the SHA-256 hash of a file's content."""
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                # Read in chunks of 4096 bytes
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception as exc:
            logger.error("Failed to compute hash for file %s: %s", file_path, exc)
            return ""

    def _should_ignore(self, rel_path: str) -> bool:
        """Determine if a file path should be ignored in the snapshot diff."""
        parts = rel_path.replace("\\", "/").lower().split("/")
        ignored_names = {
            "node_modules", ".git", ".github", "dist", "build", "runs", 
            "generated_test_files", "generated_testcases", "project-1",
            "coverage", ".pytest_cache"
        }
        for part in parts:
            if part in ignored_names:
                return True
        # Ignore specific generated test files and manifests
        if rel_path.endswith((".test.jsx", ".test.tsx", ".spec.ts", ".spec.js", "test_manifest.json", "project_meta.json", "project_index.json", "execution_report.json")):
            return True
        return False

    def create_snapshot(
        self,
        project_id: str,
        pipeline_run_id: str,
        workspace_path: str,
        framework: Optional[str] = "React"
    ) -> ProjectSnapshot:
        """Scan workspace path, compute hashes, and persist ProjectSnapshot to DB."""
        session = self._get_session()
        try:
            logger.info("Creating project snapshot for project %s, run %s at %s", project_id, pipeline_run_id, workspace_path)
            
            # Check if this snapshot already exists to prevent duplicate execution
            existing = session.query(ProjectSnapshot).filter(
                ProjectSnapshot.pipeline_run_id == pipeline_run_id
            ).first()
            if existing:
                logger.info("Snapshot for run %s already exists in database.", pipeline_run_id)
                return existing

            snapshot = ProjectSnapshot(
                project_id=project_id,
                pipeline_run_id=pipeline_run_id,
                framework=framework,
                workspace_path=workspace_path,
                created_at=datetime.utcnow()
            )
            session.add(snapshot)
            session.flush()  # Generate snapshot.id

            # Scan files
            for root, _, files in os.walk(workspace_path):
                for file in files:
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, workspace_path).replace("\\", "/")
                    
                    if self._should_ignore(rel_path):
                        continue

                    # Calculate content hash and metadata
                    content_hash = self._compute_sha256(full_path)
                    if not content_hash:
                        continue

                    file_size = os.path.getsize(full_path)
                    modified_at = datetime.utcfromtimestamp(os.path.getmtime(full_path))

                    file_snap = FileSnapshot(
                        snapshot_id=snapshot.id,
                        file_path=rel_path,
                        content_hash=content_hash,
                        file_size=file_size,
                        modified_at=modified_at
                    )
                    session.add(file_snap)

            session.commit()
            session.refresh(snapshot)
            logger.info("Successfully persisted project snapshot %s with %d files", snapshot.id, len(snapshot.file_snapshots))
            return snapshot

        except Exception as exc:
            session.rollback()
            logger.error("Failed to create project snapshot: %s", exc)
            raise
        finally:
            if self.db is None:
                session.close()

    def get_latest_snapshot(self, project_id: str) -> Optional[ProjectSnapshot]:
        """Fetch the most recent ProjectSnapshot for the given project_id."""
        session = self._get_session()
        try:
            return (
                session.query(ProjectSnapshot)
                .filter(ProjectSnapshot.project_id == project_id)
                .order_by(ProjectSnapshot.created_at.desc())
                .first()
            )
        finally:
            if self.db is None:
                session.close()

    def get_previous_snapshot(self, project_id: str, current_snapshot_id: str) -> Optional[ProjectSnapshot]:
        """Fetch the snapshot immediately preceding the current snapshot for a project."""
        session = self._get_session()
        try:
            # Query all snapshots for the project ordered descending by date
            snaps = (
                session.query(ProjectSnapshot)
                .filter(ProjectSnapshot.project_id == project_id)
                .order_by(ProjectSnapshot.created_at.desc())
                .all()
            )
            # Find the position of the current snapshot and return the next one
            for i, snap in enumerate(snaps):
                if snap.id == current_snapshot_id:
                    if i + 1 < len(snaps):
                        return snaps[i + 1]
                    break
            return None
        finally:
            if self.db is None:
                session.close()
