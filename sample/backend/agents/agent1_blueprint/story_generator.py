"""Story Generator module for Agent 1.

Generates granular user stories mapped to parent Epics, API endpoints, database tables, and acceptance criteria.
"""

import logging
from typing import Any, Dict, List
from pydantic import BaseModel, Field

from agents.agent1_blueprint.epic_generator import EpicSpec

logger = logging.getLogger(__name__)


class GeneratedStory(BaseModel):
    """Normalized User Story model for Agent 2 execution."""

    story_key: str = Field(description="Unique story ID (e.g. US001)")
    epic_key: str = Field(description="Parent Epic ID (e.g. EPIC-001)")
    title: str = Field(description="Story title")
    user_role: str = Field(default="User", description="Persona role (e.g. User, Admin)")
    goal: str = Field(description="Capability goal statement")
    benefit: str = Field(description="Business value statement")
    acceptance_criteria: List[str] = Field(default_factory=list, description="Validation criteria")
    api_endpoint: str = Field(description="Primary REST endpoint path (e.g. /api/v1/users)")
    db_table: str = Field(description="Primary database table (e.g. users)")
    target_files: Dict[str, str] = Field(default_factory=dict, description="Target file paths for Agent 2")


class StoryGenerator:
    """Generates normalized User Stories from Epics and raw stories."""

    def generate_stories(
        self,
        epics: List[EpicSpec],
        raw_stories: List[Dict[str, Any]],
    ) -> List[GeneratedStory]:
        """Produce structured user stories with target files and API endpoints."""
        stories: List[GeneratedStory] = []

        for idx, story_dict in enumerate(raw_stories):
            raw_key = story_dict.get("story_key") or f"US{idx+1:03d}"
            title = story_dict.get("title") or f"User Story {idx+1}"
            epic_key = epics[min(idx, len(epics) - 1)].epic_key

            clean_slug = title.lower().replace(" ", "_")[:20]

            stories.append(
                GeneratedStory(
                    story_key=raw_key,
                    epic_key=epic_key,
                    title=title,
                    user_role=story_dict.get("user_role", "User"),
                    goal=story_dict.get("goal") or f"Perform {title} actions",
                    benefit=story_dict.get("benefit") or "Streamline user workflow and automation",
                    acceptance_criteria=story_dict.get("acceptance_criteria") or [f"Implement {title} API", "Return 200 OK"],
                    api_endpoint=f"/api/v1/{clean_slug}s",
                    db_table=f"{clean_slug}s",
                    target_files={
                        "backend": f"backend/app/services/{clean_slug}_service.py",
                        "api": f"backend/app/api/v1/{clean_slug}_routes.py",
                        "frontend": f"frontend/src/pages/{title.replace(' ', '')}Page.tsx",
                        "database": f"backend/alembic/versions/{raw_key.lower()}_{clean_slug}_schema.py",
                        "test": f"backend/tests/test_{clean_slug}.py",
                    },
                )
            )

        return stories
