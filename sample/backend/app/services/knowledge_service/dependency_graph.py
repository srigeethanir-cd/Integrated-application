from typing import Any, Dict, List, Optional
from app.services.knowledge_service.knowledge_api import KnowledgeAPI

class DependencyGraph:
    """Represent and query dependency maps between files, components and systems."""

    def __init__(self, api: Optional[KnowledgeAPI] = None) -> None:
        self.api = api or KnowledgeAPI()

    def add_dependency(
        self,
        source_type: str,
        source_id: str,
        target_type: str,
        target_id: str,
        dep_type: str,
        created_by: str,
    ) -> None:
        """Register a dependency relationship in the database."""
        # Check if already exists
        existing = self.api.execute_query(
            "SELECT id FROM dependencies WHERE source_type = ? AND source_id = ? AND target_type = ? AND target_id = ? AND dependency_type = ?;",
            (source_type, source_id, target_type, target_id, dep_type)
        )
        if existing:
            return

        self.api.execute_query(
            "INSERT INTO dependencies (source_type, source_id, target_type, target_id, dependency_type, created_by) VALUES (?, ?, ?, ?, ?, ?);",
            (source_type, source_id, target_type, target_id, dep_type, created_by),
            commit=True
        )

    def get_dependencies_by_source(self, source_id: str) -> List[Dict[str, Any]]:
        """Fetch all outward dependency connections from a specific source."""
        return self.api.execute_query(
            "SELECT target_type, target_id, dependency_type, created_by FROM dependencies WHERE source_id = ?;",
            (source_id,)
        )

    def get_dependencies_by_target(self, target_id: str) -> List[Dict[str, Any]]:
        """Fetch all inward dependency connections targeting a specific element."""
        return self.api.execute_query(
            "SELECT source_type, source_id, dependency_type, created_by FROM dependencies WHERE target_id = ?;",
            (target_id,)
        )
