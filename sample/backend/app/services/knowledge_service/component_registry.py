from typing import Any, Dict, List, Optional
from app.services.knowledge_service.knowledge_api import KnowledgeAPI

class ComponentRegistry:
    """Registry tracking generated system components and usage maps."""

    def __init__(self, api: Optional[KnowledgeAPI] = None) -> None:
        self.api = api or KnowledgeAPI()

    def register_component(self, project_id: str, name: str, comp_type: str, story_id: Optional[str] = None) -> int:
        """Register a component under a project."""
        # Check if already exists
        existing = self.api.execute_query(
            "SELECT id FROM components WHERE project_id = ? AND name = ?;",
            (project_id, name)
        )
        if existing:
            return existing[0]["id"]

        self.api.execute_query(
            "INSERT INTO components (name, type, project_id, created_by_story_id) VALUES (?, ?, ?, ?);",
            (name, comp_type, project_id, story_id),
            commit=True
        )

        rows = self.api.execute_query(
            "SELECT id FROM components WHERE project_id = ? AND name = ?;",
            (project_id, name)
        )
        return rows[0]["id"] if rows else -1

    def get_components_by_project(self, project_id: str) -> List[Dict[str, Any]]:
        """Fetch all components registered in a project."""
        return self.api.execute_query(
            "SELECT id, name, type, created_by_story_id, created_at FROM components WHERE project_id = ?;",
            (project_id,)
        )

    def record_component_usage(self, component_id: int, story_id: str) -> None:
        """Log that an existing component was referenced/used by another story."""
        self.api.execute_query(
            "INSERT INTO component_usage (component_id, used_by_story_id) VALUES (?, ?);",
            (component_id, story_id),
            commit=True
        )
