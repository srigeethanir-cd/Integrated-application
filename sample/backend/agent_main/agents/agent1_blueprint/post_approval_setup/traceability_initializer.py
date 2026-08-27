import json
from typing import Any, Dict, List, Optional
from app.services.knowledge_service.knowledge_api import KnowledgeAPI

class TraceabilityInitializer:
    """Initialize project tracking, stories and epics metadata in the Database."""

    def __init__(self, api: Optional[KnowledgeAPI] = None) -> None:
        self.api = api or KnowledgeAPI()

    def initialize_traceability(
        self,
        project_id: str,
        project_manifest: Dict[str, Any],
        stories: List[Dict[str, Any]],
    ) -> None:
        """Seed project, epic and user story tables for downstream traceability mappings."""
        project_name = project_manifest.get("project_name", "Generated Project")
        framework = project_manifest.get("tech_stack", {}).get("backend", "python")

        # Insert project
        existing_project = self.api.execute_query("SELECT id FROM projects WHERE id = ?;", (project_id,))
        if not existing_project:
            self.api.execute_query(
                "INSERT INTO projects (id, name, framework, status) VALUES (?, ?, ?, ?);",
                (project_id, project_name, framework, "draft"),
                commit=True
            )

        # Add epics and stories
        epics_seen = set()
        for story in stories:
            epic_id = story.get("epic_id")
            if epic_id and epic_id not in epics_seen:
                epics_seen.add(epic_id)
                existing_epic = self.api.execute_query("SELECT id FROM epics WHERE id = ?;", (epic_id,))
                if not existing_epic:
                    self.api.execute_query(
                        "INSERT INTO epics (id, project_id, title) VALUES (?, ?, ?);",
                        (epic_id, project_id, f"Epic {epic_id}"),
                        commit=True
                    )

            story_id = story.get("id")
            if story_id:
                existing_story = self.api.execute_query("SELECT id FROM user_stories WHERE id = ?;", (story_id,))
                ac_json = json.dumps(story.get("acceptance_criteria", []))
                if not existing_story:
                    self.api.execute_query(
                        "INSERT INTO user_stories (id, project_id, epic_id, title, description, acceptance_criteria, status) VALUES (?, ?, ?, ?, ?, ?, ?);",
                        (story_id, project_id, epic_id, story.get("title", ""), story.get("description", ""), ac_json, "todo"),
                        commit=True
                    )
