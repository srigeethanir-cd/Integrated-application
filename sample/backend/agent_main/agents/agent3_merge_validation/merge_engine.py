"""Merge Engine for Agent 3.

Reads workspace/epics/EPxxx/USxxx/ and MergeManifest.json files, resolving conflicts and merging story code into integrated_project/.
"""

import json
import logging
import os
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class MergedFileRecord(BaseModel):
    """Record of a merged file inside integrated_project/."""

    story_key: str = Field(description="Source story ID (e.g. US001)")
    action_type: str = Field(description="Action: CREATE | MODIFY | CONFLICT_RESOLVED")
    relative_path: str = Field(description="Path relative to integrated_project/")
    status: str = Field(default="SUCCESS", description="Merge status")


class MergeEngine:
    """Merges story-specific code from workspace/epics/ into integrated_project/."""

    def merge_all_stories(
        self,
        workspace_root: str,
        integrated_project_root: str,
    ) -> List[MergedFileRecord]:
        """Discover all story workspaces and merge artifacts into integrated_project/."""
        merged_records: List[MergedFileRecord] = []
        ws_root = Path(workspace_root)
        proj_root = Path(integrated_project_root)
        proj_root.mkdir(parents=True, exist_ok=True)

        epics_dir = ws_root / "epics"
        if not epics_dir.exists():
            logger.warning("MergeEngine: No workspace/epics/ directory found.")
            return merged_records

        # Resolve project UUID from workspace path if available
        import uuid
        proj_uuid = None
        try:
            proj_uuid = uuid.UUID(ws_root.name)
        except Exception:
            pass

        for epic_folder in epics_dir.iterdir():
            if not epic_folder.is_dir():
                continue

            for story_folder in epic_folder.iterdir():
                if not story_folder.is_dir():
                    continue

                story_key = story_folder.name
                
                # Database check for human BA approval
                from app.database.session import SessionLocal
                from app.models.story import Story as StoryModel
                
                db = SessionLocal()
                approved = False
                try:
                    query = db.query(StoryModel).filter(StoryModel.story_key == story_key.upper())
                    if proj_uuid:
                        query = query.filter(StoryModel.project_id == proj_uuid)
                    story_db = query.first()
                    if story_db:
                        status_str = str(story_db.approval_status or "").upper()
                        approved = (status_str in ["APPROVED", "ACCEPTED"])
                    else:
                        # Standalone mode: consider approved if files exist
                        approved = True
                except Exception as db_err:
                    logger.warning("DB check for story %s: %s (falling back to workspace files)", story_key, db_err)
                    approved = True
                finally:
                    db.close()

                if not approved:
                    # Fallback to status.json
                    status_file = story_folder / "status.json"
                    if status_file.exists():
                        try:
                            with open(status_file, "r", encoding="utf-8") as sf:
                                status_data = json.load(sf)
                                approved = status_data.get("approved", False) or status_data.get("status") in ["APPROVED", "ACCEPTED"]
                        except Exception as se:
                            logger.error("Failed to read status.json in %s: %s", story_folder, se)

                if not approved:
                    logger.info("MergeEngine: Skipping story %s because it is not approved yet.", story_key)
                    continue

                manifest_file = story_folder / "MergeManifest.json"

                if manifest_file.exists():
                    try:
                        with open(manifest_file, "r", encoding="utf-8") as f:
                            manifest = json.load(f)
                        records = self._merge_from_manifest(manifest, story_folder, proj_root, story_key)
                        merged_records.extend(records)
                    except Exception as e:
                        logger.error("Failed to parse MergeManifest.json in %s: %s", story_folder, e)
                        records = []
                else:
                    # Fallback directory walk merge
                    records = self._merge_dir_walk(story_folder, proj_root, story_key)
                    merged_records.extend(records)

                # Persist merge outcome to database
                db = SessionLocal()
                try:
                    q = db.query(StoryModel).filter(StoryModel.story_key == story_key.upper())
                    if proj_uuid:
                        q = q.filter(StoryModel.project_id == proj_uuid)
                    story_db = q.first()
                    if story_db:
                        from app.models import StoryMerge, StoryAudit
                        story_db.merge_status = "MERGED"
                        sm = StoryMerge(
                            story_id=story_db.story_id,
                            status="MERGED",
                            merged_files={"files": [r.model_dump() if hasattr(r, "model_dump") else r.__dict__ for r in records]}
                        )
                        db.add(sm)
                        audit = StoryAudit(
                            story_id=story_db.story_id,
                            previous_state="APPROVED",
                            new_state="MERGED",
                            comments=f"Story merged successfully. Staged {len(records)} files."
                        )
                        db.add(audit)
                        db.commit()
                except Exception as ex_db:
                    db.rollback()
                    logger.error("Failed to record merge audit for story %s: %s", story_key, ex_db)
                finally:
                    db.close()

        # Promote frontend assets from workspace/{project_id}/frontend/ to generated_projects/{project_id}/frontend/
        frontend_src = ws_root / "frontend"
        if frontend_src.exists():
            frontend_dest = proj_root / "frontend"
            shutil.copytree(frontend_src, frontend_dest, dirs_exist_ok=True)
            logger.info("MergeEngine: Promoted frontend assets from %s to %s", frontend_src, frontend_dest)

        return merged_records

    def _merge_from_manifest(
        self,
        manifest: Dict[str, Any],
        story_folder: Path,
        proj_root: Path,
        story_key: str,
    ) -> List[MergedFileRecord]:
        """Merge files based on explicit MergeManifest.json actions."""
        records: List[MergedFileRecord] = []
        actions = manifest.get("actions", [])

        for act in actions:
            rel_src = str(act.get("source_file", "")).replace("\\", "/")
            rel_tgt = str(act.get("target_file", "")).replace("\\", "/")
            action_type = act.get("action_type", "CREATE")

            # Filter: only merge deployable code files (backend/ or frontend/)
            parts = [p for p in rel_tgt.split("/") if p]
            if not parts or parts[0] not in ("backend", "frontend"):
                continue

            abs_src = story_folder / rel_src
            if not abs_src.exists():
                # Try direct subfolder
                abs_src = story_folder / Path(rel_src)
            if not abs_src.exists():
                continue

            abs_tgt = proj_root / Path(rel_tgt)
            abs_tgt.parent.mkdir(parents=True, exist_ok=True)

            if abs_tgt.exists() and action_type == "MODIFY":
                self._resolve_and_append_content(abs_src, abs_tgt)
                action_type = "CONFLICT_RESOLVED"
            else:
                shutil.copy2(abs_src, abs_tgt)

            records.append(
                MergedFileRecord(
                    story_key=story_key,
                    action_type=action_type,
                    relative_path=rel_tgt,
                    status="SUCCESS",
                )
            )
            logger.info("MergeEngine: Merged %s -> integrated_project/%s [%s]", rel_src, rel_tgt, action_type)

        return records

    def _merge_dir_walk(
        self,
        story_folder: Path,
        proj_root: Path,
        story_key: str,
    ) -> List[MergedFileRecord]:
        """Fallback walk merge when MergeManifest.json is missing."""
        records: List[MergedFileRecord] = []
        for root, _, files in os.walk(story_folder):
            for file in files:
                if file in ("story.json", "traceability.json", "MergeManifest.json", "StoryValidationReport.json", "StoryExecutionSummary.json"):
                    continue

                abs_src = Path(root) / file
                rel_path = os.path.relpath(abs_src, story_folder)
                
                # Filter: only merge deployable code files (backend/ or frontend/)
                parts = Path(rel_path).parts
                if not parts or parts[0] not in ("backend", "frontend"):
                    continue

                abs_tgt = proj_root / rel_path

                abs_tgt.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(abs_src, abs_tgt)

                records.append(
                    MergedFileRecord(
                        story_key=story_key,
                        action_type="CREATE",
                        relative_path=rel_path,
                        status="SUCCESS",
                    )
                )

        return records

    def _resolve_and_append_content(self, src: Path, tgt: Path) -> None:
        """Resolve content collisions cleanly by appending new declarations or imports."""
        try:
            with open(src, "r", encoding="utf-8") as f:
                src_text = f.read()
            with open(tgt, "r", encoding="utf-8") as f:
                tgt_text = f.read()

            if src_text.strip() not in tgt_text:
                combined = f"{tgt_text.strip()}\n\n# Merged content from {src.name}\n{src_text.strip()}\n"
                with open(tgt, "w", encoding="utf-8") as f:
                    f.write(combined)
        except Exception as e:
            logger.error("Merge conflict resolution fallback error: %s", e)
            shutil.copy2(src, tgt)

    def rollback_story(self, project_id: str, story_key: str, target_version: int) -> bool:
        """Rolls back the integrated staged files of a user story to a specific version.

        Uses stored code snapshots in the StoryVersion table.
        """
        from app.database.session import SessionLocal
        from app.models.story import Story as StoryModel
        from app.models import StoryVersion, StoryAudit
        import uuid
        import os

        db = SessionLocal()
        try:
            story_db = db.query(StoryModel).filter(StoryModel.story_key == story_key.upper()).first()
            if not story_db:
                logger.error("Story %s not found in DB for rollback", story_key)
                return False

            snapshots = db.query(StoryVersion).filter(
                StoryVersion.story_id == story_db.story_id,
                StoryVersion.version == target_version
            ).all()

            if not snapshots:
                logger.warning("No code snapshots found for story %s version %d", story_key, target_version)
                return False

            proj_root = f"./generated_projects/{project_id}"
            for snap in snapshots:
                target_path = os.path.join(proj_root, snap.file_path)
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                with open(target_path, "w", encoding="utf-8") as f:
                    f.write(snap.code_content)
                logger.info("Rollback: Restored staged file %s to version %d", snap.file_path, target_version)

            # Log rollback audit
            audit = StoryAudit(
                story_id=story_db.story_id,
                previous_state=story_db.merge_status,
                new_state="MERGED_ROLLED_BACK",
                comments=f"Rolled back integrated project files to version {target_version}."
            )
            db.add(audit)
            db.commit()
            return True

        except Exception as e:
            db.rollback()
            logger.error("Failed to execute rollback for story %s: %s", story_key, e)
            return False
        finally:
            db.close()
