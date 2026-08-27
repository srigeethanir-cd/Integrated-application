import json
from typing import Any, Dict, Optional
from app.services.knowledge_service.knowledge_api import KnowledgeAPI

class BlueprintStore:
    """Read and write generated blueprints and manifestations to database."""

    def __init__(self, api: Optional[KnowledgeAPI] = None) -> None:
        self.api = api or KnowledgeAPI()

    def save_blueprint_version(self, project_id: str, version: str, manifest: Dict[str, Any], blueprint: Dict[str, Any], plan: Dict[str, Any]) -> None:
        """Create or update a project entry and insert blueprint version record."""
        # Ensure project exists
        project_name = manifest.get("project_name", "Generated Project")
        framework = tech_stack = manifest.get("tech_stack", {}).get("backend", "python")
        
        # Check if project exists
        project_exists = self.api.execute_query("SELECT id FROM projects WHERE id = ?;", (project_id,))
        if not project_exists:
            self.api.execute_query(
                "INSERT INTO projects (id, name, framework, status) VALUES (?, ?, ?, ?);",
                (project_id, project_name, framework, "draft"),
                commit=True
            )

        # Serialize full blueprint info as changes/data block
        blueprint_data = {
            "project_manifest": manifest,
            "master_blueprint": blueprint,
            "implementation_plan": plan
        }
        changes_str = json.dumps(blueprint_data)

        # Insert blueprint version
        self.api.execute_query(
            "INSERT INTO blueprint_versions (project_id, version, changes, approved_by) VALUES (?, ?, ?, ?);",
            (project_id, version, changes_str, "Agent-1"),
            commit=True
        )

    def get_blueprint_version(self, project_id: str, version: str) -> Optional[Dict[str, Any]]:
        """Retrieve blueprint payload for a specific version."""
        rows = self.api.execute_query(
            "SELECT changes FROM blueprint_versions WHERE project_id = ? AND version = ? ORDER BY approved_at DESC LIMIT 1;",
            (project_id, version)
        )
        if rows:
            return json.loads(rows[0]["changes"])
        return None

    def get_latest_version(self, project_id: str) -> Optional[str]:
        """Fetch latest version string for a project."""
        rows = self.api.execute_query(
            "SELECT version FROM blueprint_versions WHERE project_id = ? ORDER BY approved_at DESC LIMIT 1;",
            (project_id,)
        )
        if rows:
            return rows[0]["version"]
        return None
