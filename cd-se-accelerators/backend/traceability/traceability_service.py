"""Traceability Service providing matrix building, database persistence, impact analysis, and dashboard logging."""

import logging
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from traceability.impact_analyzer import ImpactAnalysisReport, ImpactAnalyzer
from traceability.log_dashboard import TraceabilityLogDashboard
from traceability.traceability_matrix import TraceabilityChain, TraceabilityMatrixBuilder

logger = logging.getLogger(__name__)


class TraceabilityService:
    """Core service for matrix management, database persistence, impact analysis, and log dashboard rendering."""

    def __init__(self, db: Optional[Session] = None):
        self.db = db
        self.matrix_builder = TraceabilityMatrixBuilder()
        self.impact_analyzer = ImpactAnalyzer()
        self.dashboard_formatter = TraceabilityLogDashboard()

    def register_story_chain(
        self,
        story_key: str,
        epic_key: str,
        title: str,
        api_endpoint: str = "/api/v1/resource",
        db_table: str = "resources",
        generated_file: str = "backend/service.py",
    ) -> TraceabilityChain:
        """Register a story's full 9-layer traceability chain and save nodes & edges into database if session provided."""
        chain = self.matrix_builder.build_chain_for_story(
            story_key=story_key,
            epic_key=epic_key,
            title=title,
            api_endpoint=api_endpoint,
            db_table=db_table,
            generated_file=generated_file,
        )

        # Add migration, shared artifact, and merge queue node traceability links
        self.matrix_builder.add_node(f"MIG-{story_key}", "MIGRATION", f"Database Migration for {story_key}")
        self.matrix_builder.add_node(f"ART-{story_key}", "SHARED_ARTIFACT", f"Shared Artifact for {story_key}")
        self.matrix_builder.add_node(f"MRG-{story_key}", "MERGE", f"Staging Merge for {story_key}")
        
        self.matrix_builder.add_edge(story_key, f"MIG-{story_key}", "MIGRATES")
        self.matrix_builder.add_edge(story_key, f"ART-{story_key}", "REGISTERS")
        self.matrix_builder.add_edge(story_key, f"MRG-{story_key}", "MERGES")



        return chain

    def analyze_change_impact(self, target_node_key: str) -> ImpactAnalysisReport:
        """Perform change impact analysis for a target node."""
        report = self.impact_analyzer.analyze_impact(self.matrix_builder, target_node_key)



        return report

    def render_log_dashboard(self, project_name: str = "AI_BA_Accelerated_App") -> str:
        """Render and output the visual ASCII log dashboard."""
        summary = self.matrix_builder.get_matrix_summary()
        return self.dashboard_formatter.display_dashboard(summary, project_name=project_name)

    def get_full_matrix(self) -> Dict[str, Any]:
        """Return full matrix node and edge structure."""
        return self.matrix_builder.get_matrix_summary()
