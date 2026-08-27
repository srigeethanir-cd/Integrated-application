"""HTTP interface for Agent-2 user story code generation and orchestration."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from pydantic import BaseModel, Field

from agents.agent2_story_generator.agent2 import Agent2StoryGenerator
from agents.agent2_story_generator.todo_app_pipeline import TodoAppAgent2Pipeline

router = APIRouter(prefix="/agent2", tags=["Agent 2"])


class Agent2ProcessStoryRequest(BaseModel):
    """Input payload for processing a single user story through Agent-2."""

    story: Dict[str, Any] = Field(..., description="User story object containing title, description, criteria")
    project_root: str = Field(..., min_length=1, description="Absolute or relative path to project root")
    blueprint: Optional[Dict[str, Any]] = None
    tech_stack: str = Field("Python FastAPI / React", description="Tech stack description")


class Agent2ProcessBatchRequest(BaseModel):
    """Input payload for processing a batch of user stories."""

    stories: List[Dict[str, Any]] = Field(..., min_length=1)
    project_root: str = Field(..., min_length=1)
    tech_stack: str = Field("Python FastAPI / React")


class Agent2RunPayload(BaseModel):
    story_key: Optional[str] = None
    story: Optional[Dict[str, Any]] = None
    project_id: Optional[str] = None
    tech_stack: str = "Python FastAPI / React TypeScript"


@router.post("/start")
def start_agent2_pipeline(background_tasks: BackgroundTasks) -> Dict[str, Any]:
    """Start Agent-2 execution pipeline for TodoApp sequentially for US001..US010."""
    pipeline = TodoAppAgent2Pipeline()
    # Initialize workspace structure immediately so files are accessible
    pipeline.initialize_workspace()
    
    # Run full generation pipeline
    background_tasks.add_task(pipeline.start_pipeline)
    
    return {
        "status": "success",
        "message": "Agent-2 execution pipeline started for TodoApp",
        "project": "TodoApp",
        "total_stories": 10,
        "provider": "Groq",
        "model": "llama-3.3-70b-versatile",
        "worker": "Agent-2"
    }


@router.post("/run")
@router.post("/process_story")
def process_story(payload: Agent2RunPayload) -> Dict[str, Any]:
    """Run Agent-2 story code generation flow with workspace isolation."""
    generator = Agent2StoryGenerator()
    story_obj = payload.story or {
        "story_key": payload.story_key or "US001",
        "title": f"User Story {payload.story_key or 'US001'}",
        "description": f"Feature implementation for {payload.story_key or 'US001'}"
    }
    res = generator.process_story(
        story=story_obj,
        project_id=payload.project_id,
        tech_stack=payload.tech_stack,
    )
    return {
        "status": "success",
        "story_key": payload.story_key or story_obj.get("story_key") or "US001",
        "summary": res
    }


@router.post("/process_batch")
def process_batch(payload: Agent2ProcessBatchRequest) -> List[Dict[str, Any]]:
    """Run Agent-2 story code generation flow for a batch of stories sequentially."""
    generator = Agent2StoryGenerator()
    results = []
    for s in payload.stories:
        res = generator.process_story(
            story=s,
            project_id=payload.project_root,
            tech_stack=payload.tech_stack,
        )
        results.append(res)
    return results
