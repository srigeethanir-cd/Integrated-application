"""Pipeline Orchestrator — Manages end-to-end execution of Agent-2 user story pipeline."""

import logging
from typing import Any, Dict, List, Optional
from agents.agent2_story_generator.agent2 import Agent2StoryGenerator

logger = logging.getLogger(__name__)


class PipelineOrchestrator:
    """Orchestrates story processing pipeline for single stories and batch queues."""

    def __init__(self, agent2_generator: Optional[Agent2StoryGenerator] = None) -> None:
        self.agent2_generator = agent2_generator or Agent2StoryGenerator()

    def process_story(
        self,
        story: Dict[str, Any],
        project_root: str,
        blueprint: Optional[Dict[str, Any]] = None,
        tech_stack: str = "Python FastAPI",
    ) -> Dict[str, Any]:
        """Process a single user story through Agent-2."""
        return self.agent2_generator.process_story(
            story=story,
            project_root=project_root,
            blueprint=blueprint,
            tech_stack=tech_stack,
        )

    def process_batch(
        self,
        stories: List[Dict[str, Any]],
        project_root: str,
        tech_stack: str = "Python FastAPI",
    ) -> List[Dict[str, Any]]:
        """Process a batch of user stories sequentially."""
        results = []
        for s in stories:
            res = self.process_story(s, project_root, tech_stack=tech_stack)
            results.append(res)
        return results
