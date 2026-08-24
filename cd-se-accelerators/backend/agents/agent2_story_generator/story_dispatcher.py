"""Story Dispatcher — Dispatches user stories for Agent-2 generation."""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class StoryDispatcher:
    """Dispatches user stories for story workspace creation and generation."""

    def __init__(self, agent2_orchestrator: Optional[Any] = None) -> None:
        self.agent2_orchestrator = agent2_orchestrator

    def dispatch_story(
        self, story: Dict[str, Any], project_root: str, tech_stack: str = "Python FastAPI"
    ) -> Dict[str, Any]:
        """Dispatch a single story to Agent-2.

        Args:
            story: User story dictionary.
            project_root: Main project root directory path.
            tech_stack: Tech stack description.

        Returns:
            Dict execution result.
        """
        if self.agent2_orchestrator:
            return self.agent2_orchestrator.process_story(story, project_root, tech_stack=tech_stack)
        
        # pyrefly: ignore [missing-import]
        from agents.agent2_story_generator.agent2 import Agent2StoryGenerator
        generator = Agent2StoryGenerator()
        return generator.process_story(story, project_root, tech_stack=tech_stack)

    def dispatch_batch(
        self, stories: List[Dict[str, Any]], project_root: str, tech_stack: str = "Python FastAPI"
    ) -> List[Dict[str, Any]]:
        """Dispatch a batch of stories sequentially."""
        results = []
        for s in stories:
            res = self.dispatch_story(s, project_root, tech_stack=tech_stack)
            results.append(res)
        return results
