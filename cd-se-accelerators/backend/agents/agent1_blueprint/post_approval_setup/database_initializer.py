import os
from typing import Optional
from app.services.knowledge_service.knowledge_api import KnowledgeAPI

class DatabaseInitializer:
    """Post-approval setup to run database DDL migrations."""

    def __init__(self, api: Optional[KnowledgeAPI] = None) -> None:
        self.api = api or KnowledgeAPI()

    def initialize_database(self) -> None:
        """Run all SQL migrations from database/migrations/ on the configured database."""
        curr_dir = os.path.dirname(os.path.abspath(__file__))
        # curr_dir is agents/agent1_blueprint/post_approval_setup
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(curr_dir)))
        migrations_dir = os.path.join(project_root, "database", "migrations")

        if not os.path.exists(migrations_dir):
            return

        migration_files = sorted([f for f in os.listdir(migrations_dir) if f.endswith(".sql")])
        for filename in migration_files:
            filepath = os.path.join(migrations_dir, filename)
            with open(filepath, "r", encoding="utf-8") as handle:
                ddl = handle.read()

            # Execute statements
            statements = [stmt.strip() for stmt in ddl.split(";") if stmt.strip()]
            for stmt in statements:
                self.api.execute_query(stmt, commit=True)
