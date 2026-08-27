import os
import sqlite3
from typing import Any, Dict, List, Optional

try:
    import psycopg
    HAS_POSTGRES = True
except ImportError:
    HAS_POSTGRES = False

class KnowledgeAPI:
    """Manager for PostgreSQL database sessions with a local SQLite fallback for testing."""

    def __init__(self, db_url: Optional[str] = None) -> None:
        self.db_url = db_url or os.getenv("DATABASE_URL")
        self.use_sqlite = not HAS_POSTGRES or not self.db_url or "sqlite" in self.db_url.lower()
        if self.use_sqlite:
            self.sqlite_path = "knowledge_service.db"

    def get_connection(self) -> Any:
        if self.use_sqlite:
            conn = sqlite3.connect(self.sqlite_path)
            conn.row_factory = sqlite3.Row
            # Enable foreign keys in sqlite
            conn.execute("PRAGMA foreign_keys = ON;")
            return conn
        else:
            # pyrefly: ignore [bad-argument-type]
            return psycopg.connect(self.db_url)

    def execute_query(self, query: str, params: Optional[tuple] = None, commit: bool = False) -> List[Dict[str, Any]]:
        """Utility to safely run query blocks."""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            if self.use_sqlite:
                cursor.execute(query, params or ())
                if commit:
                    conn.commit()
                if query.strip().lower().startswith("select"):
                    rows = cursor.fetchall()
                    return [dict(row) for row in rows]
                return []
            else:
                postgres_query = query.replace("?", "%s")
                cursor.execute(postgres_query, params or ())
                if commit:
                    conn.commit()
                if query.strip().lower().startswith("select"):
                    columns = [desc[0] for desc in cursor.description]
                    return [dict(zip(columns, row)) for row in cursor.fetchall()]
                return []
        finally:
            cursor.close()
            conn.close()
