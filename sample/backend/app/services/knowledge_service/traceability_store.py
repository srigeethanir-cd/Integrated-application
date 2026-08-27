from typing import Any, Dict, List, Optional
from app.services.knowledge_service.knowledge_api import KnowledgeAPI

class TraceabilityStore:
    """Record code revisions, testing assertions and link them directly to user stories."""

    def __init__(self, api: Optional[KnowledgeAPI] = None) -> None:
        self.api = api or KnowledgeAPI()

    def record_file_change(
        self,
        project_id: str,
        file_path: str,
        file_type: str,
        story_id: str,
        action: str,
        content: str,
        version: int,
        agent_id: str,
    ) -> None:
        """Upsert file entry and record file change in history."""
        # Ensure file exists in files table
        existing_file = self.api.execute_query(
            "SELECT id FROM files WHERE project_id = ? AND file_path = ?;",
            (project_id, file_path)
        )
        if existing_file:
            file_id = existing_file[0]["id"]
            self.api.execute_query(
                "UPDATE files SET current_version = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?;",
                (version, file_id),
                commit=True
            )
        else:
            self.api.execute_query(
                "INSERT INTO files (project_id, file_path, file_type, current_version) VALUES (?, ?, ?, ?);",
                (project_id, file_path, file_type, version),
                commit=True
            )
            rows = self.api.execute_query(
                "SELECT id FROM files WHERE project_id = ? AND file_path = ?;",
                (project_id, file_path)
            )
            file_id = rows[0]["id"]

        # Insert history record
        self.api.execute_query(
            "INSERT INTO file_history (file_id, user_story_id, action, version, content, agent_id) VALUES (?, ?, ?, ?, ?, ?);",
            (file_id, story_id, action, version, content, agent_id),
            commit=True
        )

    def record_validation_result(self, story_id: str, validator_name: str, status: str, message: str) -> None:
        """Insert validation execution metrics."""
        self.api.execute_query(
            "INSERT INTO validation_results (user_story_id, validator_name, status, message) VALUES (?, ?, ?, ?);",
            (story_id, validator_name, status, message),
            commit=True
        )

    def get_story_traceability(self, story_id: str) -> Dict[str, Any]:
        """Fetch all file changes and validations associated with a story."""
        history_rows = self.api.execute_query(
            "SELECT fh.id, f.file_path, fh.action, fh.version, fh.timestamp "
            "FROM file_history fh JOIN files f ON fh.file_id = f.id "
            "WHERE fh.user_story_id = ? ORDER BY fh.timestamp DESC;",
            (story_id,)
        )
        validation_rows = self.api.execute_query(
            "SELECT id, validator_name, status, message, timestamp "
            "FROM validation_results WHERE user_story_id = ? ORDER BY timestamp DESC;",
            (story_id,)
        )
        return {
            "story_id": story_id,
            "file_changes": history_rows,
            "validations": validation_rows
        }
