import logging
from typing import Dict, List, Set, Tuple
from app.db.models import ProjectSnapshot

logger = logging.getLogger(__name__)


class FileDiffService:
    """Detects file-level differences (added, modified, deleted) between snapshots."""

    def diff_snapshots(
        self,
        previous: ProjectSnapshot,
        current: ProjectSnapshot
    ) -> Dict[str, List[str]]:
        """Compare two project snapshots based on file path and content hashes."""
        logger.info("Diffing snapshot %s against previous snapshot %s", current.id, previous.id)
        
        # Load previous file paths and hashes
        prev_files = {f.file_path: f.content_hash for f in previous.file_snapshots}
        
        # Load current file paths and hashes
        curr_files = {f.file_path: f.content_hash for f in current.file_snapshots}

        added = []
        modified = []
        deleted = []
        unchanged = []

        # Find added, modified, unchanged files
        for path, curr_hash in curr_files.items():
            if path not in prev_files:
                added.append(path)
            elif prev_files[path] != curr_hash:
                modified.append(path)
            else:
                unchanged.append(path)

        # Find deleted files
        for path in prev_files:
            if path not in curr_files:
                deleted.append(path)

        logger.info(
            "Snapshot Diff result: added=%d, modified=%d, deleted=%d, unchanged=%d",
            len(added), len(modified), len(deleted), len(unchanged)
        )

        return {
            "added_files": sorted(added),
            "modified_files": sorted(modified),
            "deleted_files": sorted(deleted),
            "unchanged_files": sorted(unchanged),
        }
