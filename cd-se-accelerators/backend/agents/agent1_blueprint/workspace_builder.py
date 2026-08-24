"""Workspace Builder module for Agent 1.

Generates WorkspaceManifest.json and ImplementationPlan.json artifacts.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

from agents.agent1_blueprint.epic_generator import EpicSpec
from agents.agent1_blueprint.story_generator import GeneratedStory

logger = logging.getLogger(__name__)


class WorkspaceBuilder:
    """Builds workspace manifests and implementation plans for target applications."""

    def build_workspace_manifest(
        self,
        project_name: str,
        tech_stack: str,
        epics: List[EpicSpec],
        stories: List[GeneratedStory],
        dag: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate WorkspaceManifest.json dictionary."""
        return {
            "project_name": project_name,
            "tech_stack": tech_stack,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "awaiting_human_approval",
            "epics_count": len(epics),
            "stories_count": len(stories),
            "epics": [e.model_dump() for e in epics],
            "stories": [s.model_dump() for s in stories],
            "dependency_graph": dag,
            "workspace_status": {
                s.story_key: "pending" for s in stories
            },
        }

    def build_implementation_plan(
        self,
        project_name: str,
        tech_stack: str,
        stories: List[GeneratedStory],
    ) -> Dict[str, Any]:
        """Generate ImplementationPlan.json dictionary."""
        return {
            "project_name": project_name,
            "tech_stack": tech_stack,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "phases": [
                {
                    "phase": "Scaffolding & Architecture",
                    "status": "completed",
                    "description": "Project foundation, database setup, and folder structure",
                },
                {
                    "phase": "Story Execution & Merging",
                    "status": "pending",
                    "stories": [s.story_key for s in stories],
                },
                {
                    "phase": "Validation & Quality Audit",
                    "status": "pending",
                    "description": "Automated AST, security, and contract verification",
                },
            ],
        }
