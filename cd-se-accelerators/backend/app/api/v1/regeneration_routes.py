"""FastAPI Regeneration Routes for targeted story regeneration paths after BA change requests."""

import logging
import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session

from agents.agent2_story_generator import Agent2StoryGenerator
from app.core.responses import success_response
from app.database.session import get_db
from app.repository.story_repository import StoryRepository
from app.repository.generation_history_repository import GenerationHistoryRepository
from app.repository.workflow_execution_repository import WorkflowExecutionRepository

router = APIRouter(prefix="/regeneration", tags=["Targeted Regeneration"])
logger = logging.getLogger(__name__)

agent2 = Agent2StoryGenerator()


class RegenerateTargetStoriesRequest(BaseModel):
    story_keys: List[str] = Field(description="Impacted story IDs to regenerate (e.g. ['US101'])")
    feedback: Optional[str] = Field(default=None, description="BA change review feedback")


@router.post("/target-stories", response_model=Dict[str, Any])
def regenerate_target_stories(req: RegenerateTargetStoriesRequest, db: Session = Depends(get_db)) -> Any:
    """Regenerate ONLY impacted user stories for CHANGES_REQUESTED without regenerating unaffected modules."""
    logger.info("TargetedRegeneration: Regenerating impacted stories %s", req.story_keys)
    
    story_repo = StoryRepository(db)
    gen_history_repo = GenerationHistoryRepository(db)
    workflow_repo = WorkflowExecutionRepository(db)
    
    regenerated_summaries = []

    for key in req.story_keys:
        story_db = story_repo.get_by_key(key)
        if not story_db:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Story with key '{key}' not found in database."
            )
            
        project_id = str(story_db.project_id) if story_db.project_id else "PROJ-EMP-001"
        epic_key = story_db.epic.epic_key if story_db.epic else "EP001"
        
        # Load master blueprint from workflow execution session if it exists
        blueprint = {}
        exec_sess = workflow_repo.get_by_project(project_id)
        if exec_sess and exec_sess.execution_state:
            blueprint = exec_sess.execution_state.get("master_blueprint", {})
            
        story_data = {
            "story_key": story_db.story_key,
            "epic_key": epic_key.upper(),
            "title": story_db.story_title,
            "description": story_db.story_description,
            "acceptance_criteria": story_db.acceptance_criteria,
            "feedback": req.feedback,
        }
        
        t_start = time.time()
        try:
            summary = agent2.process_story(
                story=story_data,
                blueprint=blueprint,
                project_id=project_id
            )
            
            # Update story state in DB
            story_db.generation_status = "GENERATED"
            story_db.validation_status = "VALIDATED"
            story_db.preview_status = "PREVIEW_READY"
            db.add(story_db)
            
            # Save history record
            execution_time_sec = time.time() - t_start
            gen_history_repo.create({
                "story_id": story_db.story_id,
                "agent": "Agent-2 Story Generator",
                "action": "regenerate",
                "status": "SUCCESS",
                "execution_time": execution_time_sec,
            })
            
            db.commit()
            regenerated_summaries.append(summary)
        except Exception as e:
            db.rollback()
            logger.error("Failed story regeneration for %s: %s", key, e, exc_info=True)
            
            # Log failure in generation history
            try:
                gen_history_repo.create({
                    "story_id": story_db.story_id,
                    "agent": "Agent-2 Story Generator",
                    "action": "regenerate",
                    "status": "FAILED",
                    "execution_time": time.time() - t_start,
                })
                db.commit()
            except Exception:
                db.rollback()
                
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to regenerate story {key}: {e}"
            )

    return success_response(
        data={
            "regenerated_stories_count": len(regenerated_summaries),
            "affected_stories": req.story_keys,
            "unaffected_modules_preserved": True,
            "summaries": regenerated_summaries,
            "next_target": "Agent3",
        },
        message=f"Targeted regeneration completed for {len(req.story_keys)} stories.",
    )
