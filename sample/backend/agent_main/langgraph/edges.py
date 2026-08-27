"""LangGraph Edge routing logic for conditional branch execution."""

import logging
from typing import Literal

from langgraph.state import AcceleratorStateDict

logger = logging.getLogger(__name__)


def route_after_agent1(state: AcceleratorStateDict) -> Literal["agent2_node", "agent1_refinement_node", "human_approval_node"]:
    """Conditional router after Agent 1 blueprint generation."""
    status = state.get("approval_status", "PENDING")
    logger.info("LangGraph Edge Route after Agent 1: approval_status='%s'", status)

    if status == "APPROVED":
        return "agent2_node"
    elif status in ("CHANGES_REQUESTED", "REJECTED"):
        return "agent1_refinement_node"
    else:
        return "human_approval_node"


def route_after_agent2(state: AcceleratorStateDict) -> Literal["agent3_node", "agent2_node", "failure_recovery_node"]:
    """Conditional router after Agent 2 story generation."""
    agent2_out = state.get("agent2_output")
    retry = state.get("retry_count", 0)

    if agent2_out and agent2_out.get("completed_stories_count", 0) > 0:
        logger.info("LangGraph Edge Route after Agent 2: Proceeding to Agent 3 Integration")
        return "agent3_node"
    elif retry < 3:
        logger.warning("LangGraph Edge Route after Agent 2: Retrying Agent 2 (attempt %d/3)", retry + 1)
        return "agent2_node"
    else:
        return "failure_recovery_node"


def route_after_agent3(state: AcceleratorStateDict) -> Literal["END", "agent3_node", "failure_recovery_node"]:
    """Conditional router after Agent 3 system integration."""
    agent3_out = state.get("agent3_output", {})
    success = agent3_out.get("success", False)
    retry = state.get("retry_count", 0)

    if success:
        logger.info("LangGraph Edge Route after Agent 3: Pipeline Execution Successful! Route -> END")
        return "END"
    elif retry < 3:
        logger.warning("LangGraph Edge Route after Agent 3: Retrying Agent 3 (attempt %d/3)", retry + 1)
        return "agent3_node"
    else:
        return "failure_recovery_node"
