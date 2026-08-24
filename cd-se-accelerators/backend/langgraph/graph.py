"""LangGraph StateGraph builder for AI BA Accelerator workflow pipeline."""

import logging
from typing import Any, Dict, Optional

from langgraph.edges import route_after_agent1, route_after_agent2, route_after_agent3
from langgraph.nodes import (
    agent0_node,
    agent1_node,
    agent1_refinement_node,
    agent2_node,
    agent3_node,
    failure_recovery_node,
    human_approval_node,
)
from langgraph.state import AcceleratorStateDict

logger = logging.getLogger(__name__)


class StateGraphPipeline:
    """StateGraph pipeline coordinator for AI BA Accelerator workflow."""

    def __init__(self):
        self.nodes = {
            "agent0_node": agent0_node,
            "agent1_node": agent1_node,
            "human_approval_node": human_approval_node,
            "agent1_refinement_node": agent1_refinement_node,
            "agent2_node": agent2_node,
            "agent3_node": agent3_node,
            "failure_recovery_node": failure_recovery_node,
        }

    def execute_step(self, state: AcceleratorStateDict) -> AcceleratorStateDict:
        """Execute next steps in pipeline based on active state."""
        curr = state.get("current_node", "START")

        if curr == "START":
            state = agent0_node(state)
            curr = "agent0_node"

        if curr == "agent0_node":
            state = agent1_node(state)
            curr = "agent1_node"

        if curr in ("agent1_node", "human_approval_node"):
            state = human_approval_node(state)
            next_step = route_after_agent1(state)
            if next_step == "agent2_node":
                state = agent2_node(state)
                curr = "agent2_node"
            elif next_step == "agent1_refinement_node":
                state = agent1_refinement_node(state)
                curr = "agent1_refinement_node"
            else:
                return state

        if curr == "agent1_refinement_node":
            state = human_approval_node(state)
            return state

        if curr == "agent2_node":
            next_step = route_after_agent2(state)
            if next_step == "agent3_node":
                state = agent3_node(state)
                curr = "agent3_node"
            else:
                state = failure_recovery_node(state)
                return state

        if curr == "agent3_node":
            next_step = route_after_agent3(state)
            if next_step == "END":
                state["workflow_status"] = "COMPLETED"
                state["current_node"] = "END"
            else:
                state = failure_recovery_node(state)

        return state


def build_accelerator_graph() -> StateGraphPipeline:
    """Build and compile the AI BA Accelerator LangGraph workflow graph."""
    logger.info("LangGraph Graph: Compiling AI BA Accelerator StateGraph pipeline")
    return StateGraphPipeline()
