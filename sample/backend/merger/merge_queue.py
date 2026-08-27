import os
import json
import logging
import shutil
from pathlib import Path
from typing import Dict, Any, List, Set
from sqlalchemy.orm import Session
from app.models.orchestration_metadata import RollbackHistoryRecord

logger = logging.getLogger(__name__)

class DependencyAwareMergeQueue:
    """Manages the staging merge queue using a workspace JSON file and registers rollbacks in DB."""

    def __init__(self, db: Session, project_id: str, workspace_root: Path, integrated_project_root: Path):
        self.db = db
        self.project_id = project_id
        self.workspace_root = workspace_root
        self.integrated_project_root = integrated_project_root

    def load_queue(self, approved_stories: List[str]) -> Dict[str, Any]:
        """Loads or initializes merge queue statuses from a JSON file in the workspace."""
        queue_path = self.workspace_root / "metadata" / "merge_queue.json"
        if queue_path.exists():
            try:
                with open(queue_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to read merge queue JSON: {e}")
        
        # Fresh queue structure
        queue = {
            "pending": approved_stories,
            "ready": [],
            "merged": [],
            "conflicts": [],
            "rollback_backups": {}
        }
        self.save_queue(queue)
        return queue

    def save_queue(self, queue: Dict[str, Any]):
        """Persists the queue statuses to a JSON file in the workspace."""
        queue_path = self.workspace_root / "metadata" / "merge_queue.json"
        queue_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(queue_path, "w", encoding="utf-8") as f:
                json.dump(queue, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to write merge queue JSON: {e}")

    def execute_merges(
        self,
        approved_stories: List[Dict[str, Any]],
        execution_order: List[str],
        dependency_graph: Dict[str, List[str]],
        run_merge_fn: Any
    ) -> Dict[str, Any]:
        """Iterates over the queue in dependency order and performs incremental merges with rollback capabilities."""
        approved_keys = [s.get("story_key", "").upper() for s in approved_stories]
        queue = self.load_queue(approved_keys)
        
        merge_sequence = [k for k in execution_order if k in approved_keys]
        logger.info("MergeQueue: Order of merge execution: %s", merge_sequence)

        # Temporary folder for checkpoint backup files
        backup_dir = self.workspace_root / "metadata" / "rollback_backups"
        backup_dir.mkdir(parents=True, exist_ok=True)

        for s_key in merge_sequence:
            if s_key in queue["merged"]:
                continue

            deps = dependency_graph.get(s_key, [])
            unmerged_deps = [dep for dep in deps if dep in approved_keys and dep not in queue["merged"]]
            if unmerged_deps:
                logger.warning("MergeQueue: Story %s cannot be merged yet. Dependencies %s are unmerged.", s_key, unmerged_deps)
                continue

            logger.info("MergeQueue: Attempting merge of story %s...", s_key)
            if s_key not in queue["ready"]:
                queue["ready"].append(s_key)

            # Take a backup before merging this story
            backup_path = backup_dir / f"pre_{s_key.lower()}"
            if self.integrated_project_root.exists():
                shutil.copytree(self.integrated_project_root, backup_path, dirs_exist_ok=True)
                queue["rollback_backups"][s_key] = str(backup_path)

            self.save_queue(queue)

            try:
                result = run_merge_fn(s_key)
                if result.get("success"):
                    queue["merged"].append(s_key)
                    if s_key in queue["pending"]:
                        queue["pending"].remove(s_key)
                    logger.info("MergeQueue: Story %s successfully merged.", s_key)
                else:
                    raise Exception(result.get("error", "Unknown merge conflict"))
            except Exception as e:
                logger.error("MergeQueue: Merge failed for story %s. Triggering rollback: %s", s_key, e)
                queue["conflicts"].append(s_key)
                if s_key in queue["pending"]:
                    queue["pending"].remove(s_key)

                # Rollback to pre-merge backup
                if s_key in queue["rollback_backups"]:
                    pre_backup = Path(queue["rollback_backups"][s_key])
                    if pre_backup.exists():
                        shutil.rmtree(self.integrated_project_root, ignore_errors=True)
                        shutil.copytree(pre_backup, self.integrated_project_root, dirs_exist_ok=True)
                        logger.info("MergeQueue: Rollback complete to state before merging %s.", s_key)

                # Log Rollback history to PostgreSQL
                rollback_record = RollbackHistoryRecord(
                    project_id=self.project_id,
                    story_key=s_key,
                    backup_checkpoint_name=f"pre_{s_key.lower()}",
                    reason=str(e)
                )
                self.db.add(rollback_record)
                self.db.commit()

            self.save_queue(queue)

        # Cleanup backups if successful
        if not queue["conflicts"] and backup_dir.exists():
            shutil.rmtree(backup_dir, ignore_errors=True)

        return {
            "merged": queue["merged"],
            "conflicts": queue["conflicts"],
            "queue_state": queue
        }
