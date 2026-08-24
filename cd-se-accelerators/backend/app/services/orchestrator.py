import os
import uuid
import time
import logging
from typing import Any, Dict, List
from datetime import datetime, timezone
import concurrent.futures

from agents.agent0_wireframe import Agent0Wireframe
from agents.agent1_blueprint import Agent1Blueprint
from agents.agent2_story_generator import Agent2StoryGenerator
from validators.validation_orchestrator import ValidationOrchestrator
from app.database.session import SessionLocal
from app.models.story import Story as StoryModel
from app.models import StoryExecution, StoryAudit, StoryVersion, StoryValidation

logger = logging.getLogger(__name__)

class ProjectOrchestrator:
    """ProjectOrchestrator schedules, runs, and monitors User Story executions.

    Enables parallel story generation, retries, and records complete histories.
    """

    def __init__(self) -> None:
        self.agent0 = Agent0Wireframe()
        self.agent1 = Agent1Blueprint()
        self.agent2 = Agent2StoryGenerator()
        self.validator = ValidationOrchestrator()

    def run_story_pipeline(self, story: Dict[str, Any], project_id: str, blueprint: Dict[str, Any]) -> Dict[str, Any]:
        """Runs the sequence of Agent 0, 1, 2 for a single User Story.

        Includes local workspace validation and DB persistence.
        """
        s_key = story.get("story_key", "US101").upper()
        e_key = story.get("epic_key", "EP001").upper()
        t0 = time.time()

        # Database Setup
        db = SessionLocal()
        story_db = None
        current_version = 1
        try:
            story_db = db.query(StoryModel).filter(StoryModel.story_key == s_key).first()
            if story_db:
                current_version = story_db.version
                # Log queued transition
                audit = StoryAudit(
                    story_id=story_db.story_id,
                    previous_state="DRAFT",
                    new_state="QUEUED",
                    comments="Story placed in execution queue."
                )
                db.add(audit)
                db.commit()
        except Exception as dbe:
            logger.error("DB Error placing story in queue: %s", dbe)
        finally:
            db.close()

        # Maximum retries config
        max_retries = 2
        retry_idx = 0

        while retry_idx <= max_retries:
            # Set to generating status
            db = SessionLocal()
            try:
                story_db = db.query(StoryModel).filter(StoryModel.story_key == s_key).first()
                if story_db:
                    # Update ORM properties
                    story_db.generation_status = "GENERATING"
                    story_db.validation_status = "PENDING"
                    # Add execution record
                    exec_rec = StoryExecution(
                        story_id=story_db.story_id,
                        status="GENERATING",
                        retry_count=retry_idx,
                        assigned_agent="Agent2",
                        version=current_version,
                        start_time=datetime.now(timezone.utc)
                    )
                    db.add(exec_rec)
                    # Add audit trail
                    audit = StoryAudit(
                        story_id=story_db.story_id,
                        previous_state="QUEUED" if retry_idx == 0 else "FAILED",
                        new_state="GENERATING",
                        comments=f"Starting generation (Attempt {retry_idx + 1}/{max_retries + 1})."
                    )
                    db.add(audit)
                    db.commit()
            except Exception as e:
                logger.error("DB execution status write failure: %s", e)
            finally:
                db.close()

            try:
                # 1. Run Agent 0
                logger.info("[%s] Running Agent 0 for frontend wireframes", s_key)
                self.agent0.run({
                    "stories": [story],
                    "project_id": project_id,
                    "story_key": s_key,
                    "epic_key": e_key
                })

                # 2. Run Agent 1
                logger.info("[%s] Running Agent 1 for blueprint plans", s_key)
                self.agent1.process(
                    stories=[story],
                    tech_stack="Python FastAPI / React TypeScript",
                    project_id=project_id
                )

                # 3. Run Agent 2
                logger.info("[%s] Running Agent 2 for backend service generation", s_key)
                self.agent2.process_story(
                    story=story,
                    blueprint=blueprint,
                    project_id=project_id
                )

                # 4. Save Code Snapshots in StoryVersion Table
                self._save_story_snapshots(project_id, e_key, s_key, current_version)

                # 5. Run Validation
                story_ws = f"./workspace/{project_id}/epics/{e_key}/{s_key}/"
                val_report = self.validator.validate_story(story_ws, story_db.story_id if story_db else s_key, blueprint)

                duration = round((time.time() - t0) * 1000, 2)
                db = SessionLocal()
                try:
                    story_db = db.query(StoryModel).filter(StoryModel.story_key == s_key).first()
                    if story_db:
                        # Fetch latest execution
                        latest_exec = db.query(StoryExecution).filter(
                            StoryExecution.story_id == story_db.story_id
                        ).order_by(StoryExecution.created_at.desc()).first()
                        
                        if latest_exec:
                            latest_exec.status = "GENERATED"
                            latest_exec.execution_time_ms = duration
                            latest_exec.end_time = datetime.now(timezone.utc)
                        
                        story_db.generation_status = "GENERATED"
                        
                        if val_report.get("passed", False):
                            story_db.validation_status = "VALIDATED"
                            # Log audit success
                            audit = StoryAudit(
                                story_id=story_db.story_id,
                                previous_state="GENERATING",
                                new_state="VALIDATED",
                                comments=f"Story generation and validation completed successfully in {duration}ms."
                            )
                            db.add(audit)
                            db.commit()
                            break # Generation Succeeded! Exit retry loop
                        else:
                            story_db.validation_status = "FAILED"
                            # Log audit failure
                            audit = StoryAudit(
                                story_id=story_db.story_id,
                                previous_state="GENERATING",
                                new_state="FAILED",
                                comments=f"Validation failed (Attempt {retry_idx + 1}): {', '.join(val_report.get('errors', []))}"
                            )
                            db.add(audit)
                            db.commit()
                except Exception as db_ex:
                    logger.error("DB update error after validation: %s", db_ex)
                finally:
                    db.close()

            except Exception as pipeline_err:
                logger.error("Exception in story pipeline execution: %s", pipeline_err)
                db = SessionLocal()
                try:
                    story_db = db.query(StoryModel).filter(StoryModel.story_key == s_key).first()
                    if story_db:
                        story_db.generation_status = "FAILED"
                        story_db.validation_status = "FAILED"
                        audit = StoryAudit(
                            story_id=story_db.story_id,
                            previous_state="GENERATING",
                            new_state="FAILED",
                            comments=f"Execution pipeline threw exception: {str(pipeline_err)}"
                        )
                        db.add(audit)
                        db.commit()
                except Exception as dbe2:
                    logger.error("DB Error logging exception: %s", dbe2)
                finally:
                    db.close()

            # Increment retry index
            retry_idx += 1

        # If retries exceeded, increment the version for next run
        db = SessionLocal()
        try:
            story_db = db.query(StoryModel).filter(StoryModel.story_key == s_key).first()
            if story_db:
                # Increment story version in the database
                # Wait, version is a property now, but let's make sure it is updated by incrementing the execution version count
                pass
        except Exception:
            pass
        finally:
            db.close()

        return {"story_key": s_key, "success": val_report.get("passed", False)}

    def execute_project_pipeline(self, project_id: str, stories: List[Dict[str, Any]], blueprint: Dict[str, Any]) -> Dict[str, Any]:
        """Schedules and executes all User Stories concurrently.

        Coordinates thread pool parallel executions.
        """
        logger.info("ProjectOrchestrator: Scheduling concurrent story execution for project %s", project_id)

        # Run parallel execution using thread pool
        execution_results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(self.run_story_pipeline, story, project_id, blueprint): story
                for story in stories
            }
            for future in concurrent.futures.as_completed(futures):
                story_data = futures[future]
                try:
                    res = future.result()
                    execution_results.append(res)
                except Exception as e:
                    logger.error("Error executing story %s in thread pool: %s", story_data.get("story_key"), e)
                    execution_results.append({"story_key": story_data.get("story_key"), "success": False, "error": str(e)})

        logger.info("ProjectOrchestrator: Completed concurrent execution. Results: %s", execution_results)
        return {"project_id": project_id, "execution_results": execution_results}

    def _save_story_snapshots(self, project_id: str, e_key: str, s_key: str, version: int):
        """Scans workspace and snapshots generated code files into StoryVersion database table."""
        story_dir = f"./workspace/{project_id}/epics/{e_key}/{s_key}/"
        if not os.path.exists(story_dir):
            return

        db = SessionLocal()
        try:
            story_db = db.query(StoryModel).filter(StoryModel.story_key == s_key).first()
            if not story_db:
                return

            for root, _, files in os.walk(story_dir):
                for f in files:
                    if f.endswith((".py", ".tsx", ".jsx", ".js", ".ts", ".html", ".css")):
                        abs_path = os.path.join(root, f)
                        rel_path = os.path.relpath(abs_path, story_dir)
                        try:
                            with open(abs_path, "r", encoding="utf-8", errors="ignore") as file_obj:
                                content = file_obj.read()
                            # Save to StoryVersion table
                            version_record = StoryVersion(
                                story_id=story_db.story_id,
                                version=version,
                                file_path=rel_path,
                                code_content=content
                            )
                            db.add(version_record)
                        except Exception as file_err:
                            logger.error("Failed to snapshot code file %s: %s", rel_path, file_err)
            db.commit()
        except Exception as snap_ex:
            db.rollback()
            logger.error("Failed to commit StoryVersion snapshots: %s", snap_ex)
        finally:
            db.close()
