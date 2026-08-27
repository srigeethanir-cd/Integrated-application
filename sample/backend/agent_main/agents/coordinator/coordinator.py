"""Multi-Agent Coordinator orchestrating Agent 0 through Agent 3."""

import logging
from typing import Any, Dict, List, Optional

from agents.agent0_wireframe.wireframe_agent import Agent0Wireframe
from agents.agent1_blueprint.agent1 import Agent1Blueprint
from agents.agent2_story_generator.agent2 import Agent2StoryGenerator
from agents.common.llm_factory import LLMClientAdapter, LLMFactory
from agents.common.state_manager import AgentStateManager

logger = logging.getLogger(__name__)


class AgentCoordinator:
    """Central orchestration manager for Agent 0, Agent 1, Agent 2, and Agent 3."""

    def __init__(self, llm: Optional[LLMClientAdapter] = None):
        self.llm = llm or LLMFactory.create_llm_client()
        self.state_manager = AgentStateManager()

        # Initialize agents
        self.agent0 = Agent0Wireframe(llm=self.llm)
        self.agent1 = Agent1Blueprint()
        self.agent2 = Agent2StoryGenerator()

    def run_agent0(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run Agent-0 (Wireframe/Vision Spec Extraction)."""
        logger.info("Coordinator: Invoking Agent-0 Wireframe Agent")
        res = self.agent0.run(input_data)
        self.state_manager.store_artifact("agent0_output", res)
        return res

    def run_agent1(
        self,
        stories: List[Dict[str, Any]],
        tech_stack: str,
        output_dir: Optional[str] = None,
        feedback: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Run Agent-1 (Blueprint & Scaffolding Generator)."""
        logger.info("Coordinator: Invoking Agent-1 Blueprint Generator")
        res = self.agent1.process(
            stories=stories,
            tech_stack=tech_stack,
            output_dir=output_dir,
            feedback=feedback,
        )
        self.state_manager.store_artifact("blueprint_output", res)
        return res

    def run_agent2(
        self,
        story: Dict[str, Any],
        project_root: str,
        blueprint: Optional[Dict[str, Any]] = None,
        tech_stack: str = "Python FastAPI / React",
    ) -> Dict[str, Any]:
        """Run Agent-2 (Isolated Story Code Generator)."""
        logger.info("Coordinator: Invoking Agent-2 Story Generator for story %s", story.get("story_key", "US001"))
        res = self.agent2.process_story(
            story=story,
            project_root=project_root,
            blueprint=blueprint,
            tech_stack=tech_stack,
        )
        self.state_manager.store_artifact(f"story_{story.get('story_key', 'US001')}", res)
        return res

    def execute_pipeline(
        self,
        stories: List[Dict[str, Any]],
        tech_stack: str,
        project_root: str,
        wireframe_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Run full end-to-end multi-agent execution pipeline."""
        pipeline_summary = {"status": "started", "steps": {}}

        # Step 0: Wireframe (Optional)
        if wireframe_data:
            res0 = self.run_agent0(wireframe_data)
            pipeline_summary["steps"]["agent0"] = res0

        # Step 1: Blueprint
        res1 = self.run_agent1(stories=stories, tech_stack=tech_stack, output_dir=project_root)
        pipeline_summary["steps"]["agent1"] = res1

        # Step 2: Story Generations
        story_results = []
        for story in stories:
            res2 = self.run_agent2(story=story, project_root=project_root, tech_stack=tech_stack)
            story_results.append(res2)
        pipeline_summary["steps"]["agent2"] = story_results

        pipeline_summary["status"] = "completed"
        return pipeline_summary
