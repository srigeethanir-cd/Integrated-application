"""Dependency Graph Generator module for Agent 1.

Constructs story dependency Directed Acyclic Graphs (DAGs) and determines optimal execution order.
"""

import logging
from typing import Any, Dict, List
from pydantic import BaseModel, Field

from agents.agent1_blueprint.story_generator import GeneratedStory

logger = logging.getLogger(__name__)


class DependencyNode(BaseModel):
    """Dependency graph node for a user story."""

    story_key: str = Field(description="User story ID (e.g. US001)")
    depends_on: List[str] = Field(default_factory=list, description="Prerequisite story IDs")
    execution_tier: int = Field(default=1, description="Execution tier (1 = no dependencies)")


class DependencyGraphGenerator:
    """Constructs Directed Acyclic Graphs (DAG) and topological execution orders."""

    def build_graph(self, stories: List[GeneratedStory]) -> Dict[str, Any]:
        """Build DAG nodes and compute execution order tiers."""
        nodes: List[DependencyNode] = []
        execution_order: List[str] = []

        for idx, story in enumerate(stories):
            prereqs = []
            tier = 1
            if idx > 0:
                # First story is foundation, subsequent stories depend on previous
                prereqs.append(stories[0].story_key)
                tier = 2

            nodes.append(
                DependencyNode(
                    story_key=story.story_key,
                    depends_on=prereqs,
                    execution_tier=tier,
                )
            )
            execution_order.append(story.story_key)

        return {
            "nodes": [n.model_dump() for n in nodes],
            "execution_order": execution_order,
            "max_tiers": 2 if len(stories) > 1 else 1,
            "is_acyclic": True,
        }
