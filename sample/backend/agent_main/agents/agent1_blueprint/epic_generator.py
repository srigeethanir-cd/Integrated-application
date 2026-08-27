"""Epic Generator module for Agent 1.

Decomposes system scope into structured Epics with target modules, goals, and acceptance criteria.
"""

import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from agents.agent1_blueprint.requirement_analysis import RequirementSpec

logger = logging.getLogger(__name__)


class EpicSpec(BaseModel):
    """Epic specification model."""

    epic_key: str = Field(description="Unique Epic identifier (e.g. EPIC-001)")
    title: str = Field(description="Epic title")
    description: str = Field(description="Goal and scope description")
    target_module: str = Field(description="Target architectural module (e.g. auth, dashboard, core)")
    features: List[str] = Field(default_factory=list, description="Included features")


class EpicGenerator:
    """Generates structured Epics from requirement specifications and user stories."""

    def generate_epics(
        self,
        req_spec: RequirementSpec,
        stories: List[Dict[str, Any]],
    ) -> List[EpicSpec]:
        """Group requirements and stories into structured Epics."""
        epics: List[EpicSpec] = []

        # 1. Foundation & Auth Epic
        epics.append(
            EpicSpec(
                epic_key="EPIC-001",
                title="Authentication & System Core Setup",
                description="Core application setup, database infrastructure, user sign in, and token management",
                target_module="auth",
                features=["User Login", "Token Authentication", "System Configuration"],
            )
        )

        # 2. Main Feature Epics from stories
        for idx, story in enumerate(stories):
            story_key = story.get("story_key") or f"US{idx+1}"
            title = story.get("title", f"Feature Module {idx+1}")
            epics.append(
                EpicSpec(
                    epic_key=f"EPIC-00{idx+2}",
                    title=f"{title} Management",
                    description=story.get("description", f"Epic covering {title} operations"),
                    target_module=title.lower().replace(" ", "_")[:20],
                    features=[title, f"{title} API", f"{title} Database Schema"],
                )
            )

        return epics
