"""LangGraph Implementation for Agent-2 Story Generator.

Defines the Agent-2 execution state graph with nodes:
  Retrieve Context -> Decision Engine -> Prompt Builder -> LLM -> Artifact Generator -> Workspace Writer -> Validation -> Merge -> Metadata -> Complete Story
"""

import logging
from typing import Any, Dict, Optional, TypedDict

from agents.agent2_story_generator.agent2 import Agent2StoryGenerator

logger = logging.getLogger(__name__)


class Agent2GraphState(TypedDict, total=False):
    """LangGraph state schema for Agent-2."""
    story: Dict[str, Any]
    project_root: str
    tech_stack: str
    blueprint: Optional[Dict[str, Any]]
    context: Optional[Dict[str, Any]]
    decision: Optional[Dict[str, Any]]
    prompts: Optional[Dict[str, str]]
    llm_outputs: Optional[Dict[str, str]]
    artifacts: Optional[Dict[str, str]]
    story_workspace_path: Optional[str]
    validation_report: Optional[Dict[str, Any]]
    merge_result: Optional[Dict[str, Any]]
    metadata_result: Optional[str]
    status: str
    error: Optional[str]


class Agent2GraphWorkflow:
    """Encapsulates LangGraph nodes and execution flow for Agent-2."""

    def __init__(self, agent2_generator: Optional[Agent2StoryGenerator] = None) -> None:
        self.generator = agent2_generator or Agent2StoryGenerator()

    def retrieve_context_node(self, state: Agent2GraphState) -> Agent2GraphState:
        logger.info("LangGraph Node: Retrieve Context")
        state["context"] = {"story": state.get("story"), "blueprint": state.get("blueprint")}
        state["status"] = "context_retrieved"
        return state

    def decision_engine_node(self, state: Agent2GraphState) -> Agent2GraphState:
        logger.info("LangGraph Node: Decision Engine")
        story = state.get("story", {})
        blueprint = state.get("blueprint")
        decision = self.generator.decision_engine.decide(story, blueprint=blueprint)
        state["decision"] = decision
        state["status"] = "decision_made"
        return state

    def prompt_builder_node(self, state: Agent2GraphState) -> Agent2GraphState:
        logger.info("LangGraph Node: Prompt Builder")
        story = state.get("story", {})
        decision = state.get("decision", {})
        tech_stack = state.get("tech_stack", "Python FastAPI")

        prompts = {
            "backend": self.generator.backend_generator.prompt_builder.build_generation_prompt("backend", story, decision, tech_stack=tech_stack),
            "frontend": self.generator.frontend_generator.prompt_builder.build_generation_prompt("frontend", story, decision, tech_stack=tech_stack),
        }
        state["prompts"] = prompts
        state["status"] = "prompts_built"
        return state

    def llm_node(self, state: Agent2GraphState) -> Agent2GraphState:
        logger.info("LangGraph Node: LLM")
        state["status"] = "llm_completed"
        return state

    def artifact_generator_node(self, state: Agent2GraphState) -> Agent2GraphState:
        logger.info("LangGraph Node: Artifact Generator")
        story = state.get("story", {})
        decision = state.get("decision", {})
        blueprint = state.get("blueprint")
        tech_stack = state.get("tech_stack", "Python FastAPI")

        artifacts = {
            f"backend/{decision.get('module_name', 'feature')}_service.py": self.generator.backend_generator.generate(story, decision, blueprint, tech_stack),
            f"frontend/{decision.get('module_name', 'feature')}_component.jsx": self.generator.frontend_generator.generate(story, decision, blueprint, tech_stack),
        }
        state["artifacts"] = artifacts
        state["status"] = "artifacts_generated"
        return state

    def workspace_writer_node(self, state: Agent2GraphState) -> Agent2GraphState:
        logger.info("LangGraph Node: Workspace Writer")
        project_root = state.get("project_root", "")
        story = state.get("story", {})
        story_key = story.get("story_key") or story.get("key") or "US001"

        ws_path = self.generator.workspace_manager.create_story_workspace(project_root, story_key)
        self.generator.file_writer.write_batch(state.get("artifacts", {}), story_workspace_path=ws_path)

        state["story_workspace_path"] = ws_path
        state["status"] = "written_to_workspace"
        return state

    def validation_node(self, state: Agent2GraphState) -> Agent2GraphState:
        logger.info("LangGraph Node: Validation")
        ws_path = state.get("story_workspace_path")
        val_report = self.generator.validation_orchestrator.validate_story_workspace(ws_path)
        state["validation_report"] = val_report

        if not val_report.get("passed", False):
            state["status"] = "validation_failed"
            # Delete story workspace on failure
            project_root = state.get("project_root", "")
            story_key = state.get("story", {}).get("story_key", "US001")
            self.generator.workspace_manager.delete_story_workspace(project_root, story_key)
        else:
            state["status"] = "validation_passed"

        return state

    def merge_node(self, state: Agent2GraphState) -> Agent2GraphState:
        if state.get("status") != "validation_passed":
            return state

        logger.info("LangGraph Node: Merge")
        ws_path = state.get("story_workspace_path")
        project_root = state.get("project_root")
        merge_res = self.generator.story_merger.merge_story(ws_path, main_project_root=project_root)
        state["merge_result"] = merge_res
        state["status"] = "merged"
        return state

    def metadata_node(self, state: Agent2GraphState) -> Agent2GraphState:
        if state.get("status") != "merged":
            return state

        logger.info("LangGraph Node: Metadata")
        story = state.get("story", {})
        story_key = story.get("story_key") or "US001"
        project_root = state.get("project_root", "")
        ws_path = state.get("story_workspace_path", "")

        summary = {"status": "completed", "merged": True, "merged_files": state.get("merge_result", {}).get("created", [])}
        meta_file = self.generator.metadata_writer.update_metadata(story_key, summary, project_root=project_root, story_workspace_path=ws_path)
        state["metadata_result"] = meta_file
        state["status"] = "metadata_updated"
        return state

    def complete_story_node(self, state: Agent2GraphState) -> Agent2GraphState:
        logger.info("LangGraph Node: Complete Story")
        if state.get("status") == "metadata_updated":
            state["status"] = "completed"
        return state

    def execute_flow(self, story: Dict[str, Any], project_root: str, tech_stack: str = "Python FastAPI") -> Agent2GraphState:
        """Run the node sequence sequentially."""
        state: Agent2GraphState = {
            "story": story,
            "project_root": project_root,
            "tech_stack": tech_stack,
            "status": "initialized",
        }

        state = self.retrieve_context_node(state)
        state = self.decision_engine_node(state)
        state = self.prompt_builder_node(state)
        state = self.llm_node(state)
        state = self.artifact_generator_node(state)
        state = self.workspace_writer_node(state)
        state = self.validation_node(state)

        if state.get("status") == "validation_passed":
            state = self.merge_node(state)
            state = self.metadata_node(state)
            state = self.complete_story_node(state)

        return state
