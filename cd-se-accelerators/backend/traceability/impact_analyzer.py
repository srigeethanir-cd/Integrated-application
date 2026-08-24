"""Impact Analyzer for graph traversal and downstream change impact identification."""

import logging
from typing import Any, Dict, List, Set
from pydantic import BaseModel, Field

from traceability.traceability_matrix import TraceabilityEdge, TraceabilityMatrixBuilder

logger = logging.getLogger(__name__)


class ImpactAnalysisReport(BaseModel):
    """Impact analysis report model."""

    target_node_key: str = Field(description="Node key requested for change (e.g. US101, REQ-US101)")
    impacted_nodes: List[str] = Field(default_factory=list, description="Downstream impacted node keys")
    impacted_files: List[str] = Field(default_factory=list, description="Downstream impacted files")
    impacted_apis: List[str] = Field(default_factory=list, description="Downstream impacted APIs")
    impacted_db_tables: List[str] = Field(default_factory=list, description="Downstream impacted DB tables")
    impact_depth: int = Field(default=0, description="Max traversal depth")
    summary: str = Field(description="Impact analysis summary text")


class ImpactAnalyzer:
    """Performs forward and backward graph traversal to identify change impacts across all 9 architecture layers."""

    def analyze_impact(
        self,
        matrix_builder: TraceabilityMatrixBuilder,
        target_node_key: str,
    ) -> ImpactAnalysisReport:
        """Traverse graph starting at target_node_key to find all downstream impacted nodes."""
        summary_data = matrix_builder.get_matrix_summary()
        edges = summary_data.get("edges", [])

        # Build adjacency graph
        graph: Dict[str, List[str]] = {}
        for edge in edges:
            src = edge.get("source_key")
            tgt = edge.get("target_key")
            if src not in graph:
                graph[src] = []
            graph[src].append(tgt)

        # BFS / DFS traversal
        visited: Set[str] = set()
        queue = [target_node_key]
        depth = 0

        while queue:
            next_queue = []
            for node in queue:
                if node not in visited:
                    visited.add(node)
                    neighbors = graph.get(node, [])
                    next_queue.extend(neighbors)
            if next_queue:
                depth += 1
            queue = next_queue

        impacted_list = list(visited)
        files = [n for n in impacted_list if "." in n or "/" in n or "py" in n or "tsx" in n]
        apis = [n for n in impacted_list if "/api/" in n]
        dbs = [n for n in impacted_list if n.endswith("s") and not n.startswith("REQ-")]

        summary_text = (
            f"Changing target node '{target_node_key}' impacts {len(impacted_list)} total architectural nodes across "
            f"{len(files)} files, {len(apis)} API endpoints, and {len(dbs)} database tables."
        )

        logger.info("ImpactAnalyzer: Analyzed impact for %s (%d nodes affected)", target_node_key, len(impacted_list))

        return ImpactAnalysisReport(
            target_node_key=target_node_key,
            impacted_nodes=impacted_list,
            impacted_files=files,
            impacted_apis=apis,
            impacted_db_tables=dbs,
            impact_depth=depth,
            summary=summary_text,
        )
