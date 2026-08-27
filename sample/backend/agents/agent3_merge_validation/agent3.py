"""Agent-3 — Project Integration, Merge Engine, and Full System Validation Agent.

Orchestrates full application integration:
  1. Reads workspace/core/ and promotes approved shared modules to integrated_project/core/.
  2. Reads workspace/epics/EPxxx/USxxx/ and MergeManifest.json files, merging story code into integrated_project/.
  3. Resolves route, schema, and import collisions.
  4. Runs SystemValidator with a 3-attempt automated repair loop.
  5. Generates MergeReport.json, ValidationReport.json, TraceabilityReport.json, and DeploymentManifest.json.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from agents.agent3_merge_validation.merge_engine import MergeEngine
from agents.agent3_merge_validation.merge_report_generator import MergeReportGenerator
from agents.agent3_merge_validation.shared_promoter import SharedPromoter
from agents.agent3_merge_validation.system_validator import SystemValidator
from agents.common.base_agent import BaseAgent
from agents.common.llm_factory import LLMClientAdapter

logger = logging.getLogger(__name__)


class Agent3MergeValidation(BaseAgent):
    """Agent-3: Integration, Merge Engine, and Full System Validation Agent."""

    def __init__(self, llm: Optional[LLMClientAdapter] = None):
        super().__init__(
            agent_id="agent3_merge_validation",
            agent_name="Agent-3 Merge & Integration Agent",
            llm=llm,
        )
        self.shared_promoter = SharedPromoter()
        self.merge_engine = MergeEngine()
        self.system_validator = SystemValidator()
        self.report_generator = MergeReportGenerator()

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input payload containing workspace_root or integrated_project_root."""
        return "workspace_root" in input_data or "integrated_project_root" in input_data

    def format_prompt(self, input_data: Dict[str, Any]) -> str:
        """Format prompt for integration execution."""
        return f"Integrate application from workspace '{input_data.get('workspace_root', './workspace')}' into '{input_data.get('integrated_project_root', './integrated_project')}'."

    def run_integration(
        self,
        workspace_root: str = "./workspace",
        integrated_project_root: str = "./integrated_project",
    ) -> Dict[str, Any]:
        """Execute complete application integration and validation workflow."""
        logger.info("Agent3MergeValidation: Starting integration workflow from %s into %s", workspace_root, integrated_project_root)

        # 1. Promote Shared Core Modules from workspace/core/ to integrated_project/core/
        promoted_modules = self.shared_promoter.promote_shared_modules(
            workspace_root=workspace_root,
            integrated_project_root=integrated_project_root,
        )

        # 2. Merge Story-Specific Code from workspace/epics/ into integrated_project/
        merged_records = self.merge_engine.merge_all_stories(
            workspace_root=workspace_root,
            integrated_project_root=integrated_project_root,
        )

        # 3. System Validation & 3-Attempt Automated Repair Loop
        val_result = self.system_validator.validate_and_repair(
            integrated_project_root=integrated_project_root,
        )

        # 4. Generate Integration Reports & Deployment Manifest
        reports = self.report_generator.generate_all_reports(
            integrated_project_root=integrated_project_root,
            promoted_modules=promoted_modules,
            merged_records=merged_records,
            val_result=val_result,
        )

        logger.info(
            "Agent3MergeValidation: Integration COMPLETED. Overall passed: %s (Promoted %d shared modules, Merged %d files)",
            val_result.overall_passed,
            len(promoted_modules),
            len(merged_records),
        )

        # Database persistence logic
        proj_uuid = self._resolve_project_id(workspace_root, integrated_project_root)
        if proj_uuid:
            from app.database.session import SessionLocal
            from app.models.consolidated_models import ExecutionLog, ProjectValidation
            
            db = SessionLocal()
            try:
                # 1. Insert ExecutionLog
                execution_record = ExecutionLog(
                    project_id=proj_uuid,
                    agent_name="Agent3",
                    stage="Integration & Validation",
                    execution_state="SUCCESS" if val_result.overall_passed else "FAILED",
                    inputs_json={"workspace_root": workspace_root, "integrated_project_root": integrated_project_root},
                    outputs_json={
                        "success": val_result.overall_passed,
                        "promoted_shared_modules_count": len(promoted_modules),
                        "merged_files_count": len(merged_records),
                        "validation_attempts": val_result.attempts_executed
                    }
                )
                db.add(execution_record)
                logger.info("Agent3MergeValidation: Staged ExecutionLog record.")

                # 2. Insert ProjectValidation if validation was successful
                if val_result.overall_passed:
                    validation_record = ProjectValidation(
                        project_id=proj_uuid,
                        validation_status="PASSED",
                        build_status="SUCCESS",
                        validator_name="SystemValidator",
                        passed=True,
                        validation_score=100.0,
                        report=reports.get("validation_report", {})
                    )
                    db.add(validation_record)
                    logger.info("Agent3MergeValidation: Staged ProjectValidation record.")

                db.commit()
                logger.info("Agent3MergeValidation: Successfully committed Agent-3 execution logs and validation records to database.")
            except Exception as e:
                db.rollback()
                logger.error("Agent3MergeValidation: Failed to persist execution logs/validation results: %s", e, exc_info=True)
            finally:
                db.close()
        else:
            logger.warning("Agent3MergeValidation: Aborted database logging due to unresolved project ID.")

        return {
            "success": val_result.overall_passed,
            "agent_id": self.agent_id,
            "integrated_project_root": integrated_project_root,
            "promoted_shared_modules_count": len(promoted_modules),
            "merged_files_count": len(merged_records),
            "validation_attempts": val_result.attempts_executed,
            "reports": reports,
            "deployment_manifest": reports.get("deployment_manifest", {}),
        }

    def _resolve_project_id(self, workspace_root: str, integrated_project_root: str) -> Optional[Any]:
        import re
        import uuid
        from app.database.session import SessionLocal
        from app.models.project import Project
        from app.models.story import Story as StoryModel

        db = SessionLocal()
        try:
            # 1. Try to extract UUIDs from workspace_root and integrated_project_root paths
            uuid_pattern = re.compile(r'[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}')
            paths_to_check = [workspace_root, integrated_project_root]
            for path_str in paths_to_check:
                if not path_str:
                    continue
                for match in uuid_pattern.finditer(path_str):
                    try:
                        candidate_uuid = uuid.UUID(match.group(0))
                        proj = db.query(Project).filter(Project.project_id == candidate_uuid).first()
                        if proj:
                            logger.info("Agent3MergeValidation: Resolved project ID %s from path '%s'", candidate_uuid, path_str)
                            return proj.project_id
                    except ValueError:
                        pass

            # 2. Try to resolve via stories in workspace
            ws_root = Path(workspace_root)
            epics_dir = ws_root / "epics"
            if epics_dir.exists():
                for epic_folder in epics_dir.iterdir():
                    if not epic_folder.is_dir():
                        continue
                    for story_folder in epic_folder.iterdir():
                        if not story_folder.is_dir():
                            continue
                        story_key = story_folder.name.upper()
                        story_db = db.query(StoryModel).filter(StoryModel.story_key == story_key).first()
                        if story_db and story_db.project_id:
                            logger.info("Agent3MergeValidation: Resolved project ID %s from story '%s'", story_db.project_id, story_key)
                            return story_db.project_id

            # 3. Try to lookup workspace folder name in projects
            folder_name = ws_root.name
            try:
                folder_uuid = uuid.UUID(folder_name)
                proj = db.query(Project).filter(Project.project_id == folder_uuid).first()
                if proj:
                    logger.info("Agent3MergeValidation: Resolved project ID %s from folder name UUID", proj.project_id)
                    return proj.project_id
            except ValueError:
                pass

            proj = db.query(Project).filter(Project.project_name == folder_name).first()
            if proj:
                logger.info("Agent3MergeValidation: Resolved project ID %s from folder name project_name", proj.project_id)
                return proj.project_id

        except Exception as e:
            logger.error("Agent3MergeValidation: Error during project resolution: %s", e)
        finally:
            db.close()

        logger.warning("Agent3MergeValidation: Could not resolve project_id from execution paths, stories, or database metadata.")
        return None
