"""Traceability Matrix Builder establishing 9-layer relationships across software architecture."""

import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class TraceabilityNode(BaseModel):
    """Pydantic model for a traceability node."""

    node_key: str = Field(description="Unique node identifier (e.g. REQ-US101, EPIC-001, US101, API-USER)")
    node_type: str = Field(description="Type: REQ | EPIC | STORY | COMPONENT | API | DB | TEST | FILE | REPORT")
    name: str = Field(description="Display title or name")
    status: str = Field(default="ACTIVE", description="Node status: ACTIVE | MODIFIED | DEPRECATED")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Custom node metadata")


class TraceabilityEdge(BaseModel):
    """Pydantic model for a directed relationship edge."""

    source_key: str = Field(description="Source node key")
    target_key: str = Field(description="Target node key")
    relationship_type: str = Field(description="Type: IMPLEMENTS | EXPOSES | USES | STORES | TESTS | GENERATES | VALIDATES")


class TraceabilityChain(BaseModel):
    """Full 9-layer traceability chain for a User Story."""

    requirement_id: str
    epic_id: str
    story_id: str
    component_id: str
    api_endpoint: str
    database_table: str
    test_id: str
    generated_file: str
    validation_report_id: str


class TraceabilityMatrixBuilder:
    """Builds and manages the 9-layer relationship matrix across software architecture."""

    def __init__(self):
        self._nodes: Dict[str, TraceabilityNode] = {}
        self._edges: List[TraceabilityEdge] = []

    def add_node(self, node_key: str, node_type: str, name: str, metadata: Optional[Dict[str, Any]] = None) -> TraceabilityNode:
        """Register a node in the traceability matrix."""
        node = TraceabilityNode(
            node_key=node_key,
            node_type=node_type,
            name=name,
            status="ACTIVE",
            metadata=metadata or {},
        )
        self._nodes[node_key] = node
        return node

    def add_edge(self, source_key: str, target_key: str, relationship_type: str) -> TraceabilityEdge:
        """Register a directed relationship edge."""
        edge = TraceabilityEdge(
            source_key=source_key,
            target_key=target_key,
            relationship_type=relationship_type,
        )
        self._edges.append(edge)
        return edge

    def build_chain_for_story(
        self,
        story_key: str,
        epic_key: str,
        title: str,
        api_endpoint: str = "/api/v1/resource",
        db_table: str = "resources",
        generated_file: str = "backend/service.py",
    ) -> TraceabilityChain:
        """Construct a full 9-layer traceability chain for a user story and register nodes/edges."""
        req_id = f"REQ-{story_key}"
        comp_id = f"COMP-{title.replace(' ', '')}"
        test_id = f"TEST-{story_key}"
        report_id = f"REPORT-{story_key}"

        # Register 9 nodes
        self.add_node(req_id, "REQ", f"Requirement for {title}")
        self.add_node(epic_key, "EPIC", f"Epic {epic_key}")
        self.add_node(story_key, "STORY", title)
        self.add_node(comp_id, "COMPONENT", f"React UI {comp_id}")
        self.add_node(api_endpoint, "API", f"REST Endpoint {api_endpoint}")
        self.add_node(db_table, "DB", f"SQL Table {db_table}")
        self.add_node(test_id, "TEST", f"Pytest Suite {test_id}")
        self.add_node(generated_file, "FILE", f"Source Code {generated_file}")
        self.add_node(report_id, "REPORT", f"Validation Report {report_id}")

        # Register 8 directional edges forming 9-layer chain
        self.add_edge(req_id, epic_key, "INCLUDES")
        self.add_edge(epic_key, story_key, "CONTAINS")
        self.add_edge(story_key, comp_id, "IMPLEMENTS_UI")
        self.add_edge(comp_id, api_endpoint, "CALLS_API")
        self.add_edge(api_endpoint, db_table, "STORES_IN")
        self.add_edge(story_key, test_id, "TESTS_WITH")
        self.add_edge(story_key, generated_file, "GENERATES_FILE")
        self.add_edge(generated_file, report_id, "VALIDATES_IN")

        return TraceabilityChain(
            requirement_id=req_id,
            epic_id=epic_key,
            story_id=story_key,
            component_id=comp_id,
            api_endpoint=api_endpoint,
            database_table=db_table,
            test_id=test_id,
            generated_file=generated_file,
            validation_report_id=report_id,
        )

    def get_matrix_summary(self) -> Dict[str, Any]:
        """Return full matrix node and edge counts."""
        return {
            "total_nodes": len(self._nodes),
            "total_edges": len(self._edges),
            "node_types": list(set(n.node_type for n in self._nodes.values())),
            "nodes": [n.model_dump() for n in self._nodes.values()],
            "edges": [e.model_dump() for e in self._edges],
        }
