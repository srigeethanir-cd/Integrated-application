"""Requirement Analysis module for Agent 1.

Analyzes raw user stories, tech stack, and Agent 0 UI metadata into domain entity models, API endpoints, and NFR requirements.
"""

import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from agents.common.llm_factory import LLMClientAdapter

logger = logging.getLogger(__name__)


class DomainEntity(BaseModel):
    """Domain database entity specification."""

    entity_name: str = Field(description="Name of the domain entity (e.g. User, Project, Story)")
    table_name: str = Field(description="SQL table name (e.g. users, projects, stories)")
    attributes: List[Dict[str, str]] = Field(default_factory=list, description="Column names and data types")


class RequirementSpec(BaseModel):
    """Normalized technical requirement specification."""

    project_name: str = Field(default="GeneratedApp", description="Target application name")
    project_description: str = Field(default="", description="High-level project summary/goal")
    tech_stack: str = Field(default="Python FastAPI / React TypeScript", description="Tech stack description")
    entities: List[DomainEntity] = Field(default_factory=list, description="Extracted domain entities")
    nfrs: List[str] = Field(default_factory=list, description="Non-functional requirements")
    api_prefixes: List[str] = Field(default_factory=lambda: ["/api/v1"], description="API route prefixes")


class RequirementAnalysis:
    """Technical requirement analyzer combining user stories, tech stack, and UI metadata."""

    def __init__(self, llm: Optional[LLMClientAdapter] = None):
        self.llm = llm

    def analyze(
        self,
        stories: List[Dict[str, Any]],
        tech_stack: str,
        project_name: Optional[str] = None,
        project_description: Optional[str] = None,
        ui_metadata: Optional[Dict[str, Any]] = None,
    ) -> RequirementSpec:
        """Analyze stories and tech stack to produce normalized technical requirement spec."""
        proj_name = project_name or "Employee Management System"
        proj_desc = project_description or "AI Accelerated Application"

        entities = [
            DomainEntity(
                entity_name="User",
                table_name="users",
                attributes=[
                    {"name": "id", "type": "String(36)"},
                    {"name": "email", "type": "String(255)"},
                    {"name": "password_hash", "type": "String(255)"},
                    {"name": "role", "type": "String(50)"},
                ],
            ),
            DomainEntity(
                entity_name="Project",
                table_name="projects",
                attributes=[
                    {"name": "id", "type": "String(36)"},
                    {"name": "name", "type": "String(255)"},
                    {"name": "tech_stack", "type": "String(255)"},
                    {"name": "status", "type": "String(50)"},
                ],
            ),
        ]

        # Extract entities from stories
        for story in stories:
            title = story.get("title", "")
            words = [w.capitalize() for w in title.split() if w.isalpha() and len(w) > 3]
            if words:
                name = words[0]
                if name not in [e.entity_name for e in entities]:
                    entities.append(
                        DomainEntity(
                            entity_name=name,
                            table_name=f"{name.lower()}s",
                            attributes=[
                                {"name": "id", "type": "String(36)"},
                                {"name": "name", "type": "String(255)"},
                                {"name": "description", "type": "Text"},
                            ],
                        )
                    )

        nfrs = [
            "API response time < 200ms",
            "JWT bearer token authentication",
            "SQLAlchemy 2.0 async/sync ORM compatibility",
            "React Router v6 lazy-loaded SPA routes",
        ]

        return RequirementSpec(
            project_name=proj_name,
            project_description=proj_desc,
            tech_stack=tech_stack,
            entities=entities,
            nfrs=nfrs,
        )

