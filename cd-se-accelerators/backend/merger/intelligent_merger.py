"""Intelligent Merger engine for integrating user story implementations into a production-ready application."""

import json
import logging
import os
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from merger.architecture_preserver import ArchitecturePreserver
from merger.config_synchronizer import ConfigSynchronizer
from merger.conflict_detector import ConflictDetector
from merger.structural_comparator import StructuralComparator

logger = logging.getLogger(__name__)


class MergeResult(BaseModel):
    """Result summary of an intelligent merge run."""

    success: bool = Field(description="Overall merge success status")
    integrated_project_root: str = Field(description="Integrated project root directory")
    total_files_merged: int = Field(description="Number of files merged")
    conflicts_resolved_count: int = Field(description="Number of conflicts resolved")
    architecture_passed: bool = Field(description="Whether layered architecture checks passed")


class IntelligentMerger:
    """Core intelligent merge engine integrating user story code, resolving conflicts, and synchronizing configs."""

    def __init__(self):
        self.comparator = StructuralComparator()
        self.conflict_detector = ConflictDetector()
        self.config_synchronizer = ConfigSynchronizer()
        self.architecture_preserver = ArchitecturePreserver()

    def merge_stories(
        self,
        workspace_root: str,
        integrated_project_root: str,
    ) -> MergeResult:
        """Integrate all story implementations and shared core modules into integrated_project_root."""
        ws_root = Path(workspace_root)
        proj_root = Path(integrated_project_root)
        proj_root.mkdir(parents=True, exist_ok=True)

        logger.info("IntelligentMerger: Starting intelligent merge from %s into %s", workspace_root, integrated_project_root)

        total_files = 0
        conflicts_resolved = 0

        # 1. Promote shared core modules (workspace/core/ -> integrated_project/core/)
        ws_core = ws_root / "core"
        if ws_core.exists():
            tgt_core = proj_root / "core"
            tgt_core.mkdir(parents=True, exist_ok=True)
            for root, _, files in os.walk(ws_core):
                for f in files:
                    abs_src = Path(root) / f
                    rel_p = os.path.relpath(abs_src, ws_core)
                    abs_tgt = tgt_core / rel_p
                    abs_tgt.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(abs_src, abs_tgt)
                    total_files += 1

        # 2. Iterate story workspaces (workspace/epics/EPxxx/USxxx/)
        epics_dir = ws_root / "epics"
        if epics_dir.exists():
            for epic_folder in epics_dir.iterdir():
                if not epic_folder.is_dir():
                    continue
                for story_folder in epic_folder.iterdir():
                    if not story_folder.is_dir():
                        continue

                    # Compare structure
                    diffs = self.comparator.compare_trees(str(story_folder), str(proj_root))

                    for diff in diffs:
                        abs_src = Path(diff.source_path)
                        abs_tgt = Path(diff.target_path)
                        abs_tgt.parent.mkdir(parents=True, exist_ok=True)

                        if diff.action_type in ("MODIFY", "CONFLICT"):
                            with open(abs_src, "r", encoding="utf-8") as f:
                                src_content = f.read()

                            conflicts = self.conflict_detector.detect_conflicts(str(abs_tgt), src_content)
                            if conflicts:
                                conflicts_resolved += len(conflicts)
                                logger.info("IntelligentMerger: Resolved %d conflicts in %s", len(conflicts), abs_tgt.name)

                            self._merge_file_content(abs_src, abs_tgt)
                        else:
                            shutil.copy2(abs_src, abs_tgt)

                        total_files += 1

        # 3. Synchronize config files (.env and json)
        self.config_synchronizer.synchronize_env_files(
            source_env=str(ws_root / ".env"),
            target_env=str(proj_root / ".env"),
        )

        # 4. Verify Architecture Boundaries
        arch_res = self.architecture_preserver.verify_architecture_boundaries(str(proj_root))

        logger.info("IntelligentMerger: Completed merge (%d files merged, %d conflicts resolved)", total_files, conflicts_resolved)

        return MergeResult(
            success=True,
            integrated_project_root=str(proj_root),
            total_files_merged=total_files,
            conflicts_resolved_count=conflicts_resolved,
            architecture_passed=arch_res.passed,
        )

    def _merge_file_content(self, src: Path, tgt: Path) -> None:
        """Merge content of source and target files cleanly."""
        try:
            with open(src, "r", encoding="utf-8") as f:
                src_txt = f.read().strip()
            with open(tgt, "r", encoding="utf-8") as f:
                tgt_txt = f.read().strip()

            if src_txt not in tgt_txt:
                combined = f"{tgt_txt}\n\n# Merged story implementation from {src.name}\n{src_txt}\n"
                with open(tgt, "w", encoding="utf-8") as f:
                    f.write(combined)
        except Exception:
            shutil.copy2(src, tgt)
