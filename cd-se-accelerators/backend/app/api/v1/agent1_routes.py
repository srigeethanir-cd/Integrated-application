"""HTTP interface for the Agent-1 blueprint generation workflow."""

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from agents.agent1_blueprint.agent1 import Agent1Blueprint

router = APIRouter(prefix="/agent1", tags=["Agent 1"])


class Agent1GenerateRequest(BaseModel):
    """Input needed to generate an approval-ready architecture blueprint."""

    stories: list[dict[str, Any]] = Field(min_length=1)
    tech_stack: str = Field(min_length=1)


@router.post("/generate")
def generate_blueprint(payload: Agent1GenerateRequest) -> dict[str, Any]:
    """Run Agent-1 using the LLM provider configured in the backend `.env` file."""
    return Agent1Blueprint().process(payload.stories, payload.tech_stack)
