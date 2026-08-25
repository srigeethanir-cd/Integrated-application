# backend/app/services/dependency/dependency_graph.py
"""Dependency Graph module.

Constructs a directed graph representing import relationships between files.
Uses ``networkx`` for graph representation. Actual graph building logic will be added later.
"""

from __future__ import annotations

from typing import List, Tuple

import networkx as nx


class DependencyGraph:
    """Build and query a dependency graph for a codebase.

    The graph is a ``networkx.DiGraph`` where nodes are file paths and edges
    represent import relationships.
    """

    def __init__(self) -> None:
        """Initialize an empty directed graph."""
        self.graph: nx.DiGraph = nx.DiGraph()

    def add_edges(self, edges: List[Tuple[str, str]]) -> None:
        """Add a list of ``(source, target)`` edges to the graph.

        Args:
            edges: List of tuple pairs where each element is a file path.
        """
        self.graph.add_edges_from(edges)

    def detect_cycles(self) -> List[List[str]]:
        """Return a list of cycles detected in the graph.

        Each cycle is represented as an ordered list of file paths.
        """
        return [list(cycle) for cycle in nx.simple_cycles(self.graph)]

    def to_adjacency_dict(self) -> dict[str, List[str]]:
        """Serialize the graph to an adjacency‑list dictionary.

        Returns:
            ``{source: [target, ...], ...}``
        """
        return {
            str(node): [str(target) for target in self.graph.successors(node)]
            for node in self.graph.nodes
        }
