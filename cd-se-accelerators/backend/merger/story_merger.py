"""Story Merger — Merges Story Workspace into Main Project.

Performs atomic merge operations after story workspace validation succeeds:
- Create
- Modify
- Delete
- Section Merge
- Conflict Detection
- Atomic Merge & Rollback
"""

import os
import shutil
import hashlib
import logging
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class MergeConflictError(Exception):
    """Raised when conflict is detected during story merge."""
    pass


class MergeExecutionError(Exception):
    """Raised when error occurs during atomic merge operation."""
    pass


class StoryMerger:
    """Merges validated code artifacts from Story Workspace into Main Project."""

    def __init__(self, project_root: Optional[str] = None) -> None:
        self.project_root = project_root

    @staticmethod
    def _calculate_hash(content: str) -> str:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def detect_conflicts(
        self, story_workspace_path: str, main_project_root: str
    ) -> List[Dict[str, Any]]:
        """Detect conflicts between story workspace and main project files.

        Returns list of conflict items if any.
        """
        conflicts = []
        for root, _, files in os.walk(story_workspace_path):
            for f in files:
                abs_ws_file = os.path.join(root, f)
                rel_path = os.path.relpath(abs_ws_file, story_workspace_path)

                # Skip workspace internal folders
                first_part = rel_path.split(os.sep)[0]
                if first_part in ("metadata", "validation", "logs"):
                    continue

                abs_main_file = os.path.join(main_project_root, rel_path)
                if os.path.exists(abs_main_file):
                    # Check if file has been modified concurrently
                    with open(abs_ws_file, "r", encoding="utf-8", errors="ignore") as ws_f:
                        ws_content = ws_f.read()
                    with open(abs_main_file, "r", encoding="utf-8", errors="ignore") as main_f:
                        main_content = main_f.read()

                    # Simple hash collision check for conflict
                    if ws_content != main_content and "CONFLICT_MARKER" in main_content:
                        conflicts.append({
                            "rel_path": rel_path,
                            "type": "unresolved_conflict",
                            "main_path": abs_main_file,
                            "ws_path": abs_ws_file,
                        })
        return conflicts

    def section_merge_python(self, main_content: str, story_content: str) -> str:
        """Perform section-level smart merge for Python files (e.g. merge imports & functions)."""
        main_lines = main_content.splitlines()
        story_lines = story_content.splitlines()

        # Extract imports from story that are missing in main
        main_import_set = set(line.strip() for line in main_lines if line.startswith("import ") or line.startswith("from "))
        story_imports = [line for line in story_lines if (line.startswith("import ") or line.startswith("from ")) and line.strip() not in main_import_set]

        merged_lines = list(main_lines)
        if story_imports:
            # Insert new imports after last import in main_lines
            last_import_idx = 0
            for idx, line in enumerate(main_lines):
                if line.startswith("import ") or line.startswith("from "):
                    last_import_idx = idx + 1
            merged_lines = main_lines[:last_import_idx] + story_imports + main_lines[last_import_idx:]

        # Append new top-level functions/classes from story not present in main
        main_full_text = "\n".join(merged_lines)
        story_blocks = []
        current_block = []
        for line in story_lines:
            if (line.startswith("def ") or line.startswith("class ")) and current_block:
                story_blocks.append("\n".join(current_block))
                current_block = [line]
            elif current_block or line.startswith("def ") or line.startswith("class "):
                current_block.append(line)
        if current_block:
            story_blocks.append("\n".join(current_block))

        for block in story_blocks:
            first_line = block.splitlines()[0]
            func_or_class_name = first_line.split("(")[0].split(":")[0].strip()
            if func_or_class_name not in main_full_text:
                merged_lines.append("\n" + block)

        return "\n".join(merged_lines)

    def merge_story(
        self,
        story_workspace_path: str,
        main_project_root: Optional[str] = None,
        deleted_files: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Merge Story Workspace into Main Project atomically.

        Args:
            story_workspace_path: Path to workspace/<story_id>.
            main_project_root: Path to outputs/projects/<project_name>.
            deleted_files: Relative paths of files to remove from main project.

        Returns:
            Dict summary of merged files and actions taken.
        """
        root_dir = main_project_root or self.project_root
        if not root_dir:
            raise ValueError("Main project root path must be specified.")

        conflicts = self.detect_conflicts(story_workspace_path, root_dir)
        if conflicts:
            raise MergeConflictError(f"Merge conflicts detected in {len(conflicts)} files.")

        # Create temporary backup for atomic rollback
        backup_dir = os.path.join(root_dir, ".merge_backup")
        if os.path.exists(backup_dir):
            shutil.rmtree(backup_dir, ignore_errors=True)

        created_files = []
        modified_files = []
        removed_files = []

        try:
            # Make backup of existing files in main_project_root
            os.makedirs(backup_dir, exist_ok=True)
            for root, _, files in os.walk(story_workspace_path):
                for f in files:
                    abs_ws_file = os.path.join(root, f)
                    rel_path = os.path.relpath(abs_ws_file, story_workspace_path)
                    first_part = rel_path.split(os.sep)[0]
                    if first_part in ("metadata", "validation", "logs"):
                        continue

                    abs_main_file = os.path.join(root_dir, rel_path)
                    if os.path.exists(abs_main_file):
                        abs_backup_file = os.path.join(backup_dir, rel_path)
                        os.makedirs(os.path.dirname(abs_backup_file), exist_ok=True)
                        shutil.copy2(abs_main_file, abs_backup_file)

            # Perform merge operations
            for root, _, files in os.walk(story_workspace_path):
                for f in files:
                    abs_ws_file = os.path.join(root, f)
                    rel_path = os.path.relpath(abs_ws_file, story_workspace_path)

                    first_part = rel_path.split(os.sep)[0]
                    if first_part in ("metadata", "validation", "logs"):
                        continue

                    abs_main_file = os.path.join(root_dir, rel_path)
                    os.makedirs(os.path.dirname(abs_main_file), exist_ok=True)

                    with open(abs_ws_file, "r", encoding="utf-8", errors="ignore") as ws_f:
                        ws_content = ws_f.read()

                    if not os.path.exists(abs_main_file):
                        with open(abs_main_file, "w", encoding="utf-8") as main_f:
                            main_f.write(ws_content)
                        created_files.append(rel_path)
                    else:
                        with open(abs_main_file, "r", encoding="utf-8", errors="ignore") as main_f:
                            main_content = main_f.read()

                        # Smart section merge for python files, overwrite for others
                        if rel_path.endswith(".py"):
                            merged_content = self.section_merge_python(main_content, ws_content)
                        else:
                            merged_content = ws_content

                        with open(abs_main_file, "w", encoding="utf-8") as main_f:
                            main_f.write(merged_content)
                        modified_files.append(rel_path)

            # Handle explicit file deletions if specified
            if deleted_files:
                for del_rel in deleted_files:
                    abs_del = os.path.join(root_dir, del_rel)
                    if os.path.exists(abs_del):
                        os.remove(abs_del)
                        removed_files.append(del_rel)

            # Clean up backup on success
            shutil.rmtree(backup_dir, ignore_errors=True)
            logger.info("Successfully merged story workspace into main project.")

            return {
                "status": "success",
                "created": created_files,
                "modified": modified_files,
                "deleted": removed_files,
                "total_merged": len(created_files) + len(modified_files),
            }

        except Exception as e:
            logger.error("Atomic merge failed, rolling back changes: %s", str(e))
            self.rollback(root_dir, backup_dir)
            raise MergeExecutionError(f"Merge failed and was rolled back: {str(e)}") from e

    def rollback(self, main_project_root: str, backup_dir: str) -> None:
        """Rollback main project to backup state."""
        if not os.path.exists(backup_dir):
            return

        for root, _, files in os.walk(backup_dir):
            for f in files:
                abs_backup = os.path.join(root, f)
                rel_path = os.path.relpath(abs_backup, backup_dir)
                abs_main = os.path.join(main_project_root, rel_path)
                os.makedirs(os.path.dirname(abs_main), exist_ok=True)
                shutil.copy2(abs_backup, abs_main)

        shutil.rmtree(backup_dir, ignore_errors=True)
        logger.info("Rollback complete for main project.")
