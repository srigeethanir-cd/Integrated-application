import os
import re
import logging
from pathlib import Path
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class CrossStoryValidator:
    """Executes pre-merge validations across multiple approved stories to detect interface/schema collisions."""

    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root

    def validate_cross_stories(self, approved_stories: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Runs checks across all approved user stories. Returns validation report and list of failed stories."""
        passed = True
        errors = []
        failed_stories = set()

        api_routes = {}
        database_tables = set()

        # Step 1: Scan individual story sandboxes for endpoints and tables
        for story in approved_stories:
            s_key = story.get("story_key", "").upper()
            e_key = story.get("epic_key", "").upper()
            story_dir = self.workspace_root / "epics" / e_key / s_key

            if not story_dir.exists():
                continue

            # Scan backend for API routes and check collisions
            backend_dir = story_dir / "backend"
            if backend_dir.exists():
                for py_file in backend_dir.glob("*.py"):
                    try:
                        content = py_file.read_text(encoding="utf-8")
                        # Match route decorators, e.g. @router.get("/api/v1/users")
                        matches = re.findall(r"@router\.(get|post|put|delete|patch)\((['\"])(.*?)\2", content)
                        for method, _, path in matches:
                            route_key = f"{method.upper()}:{path}"
                            if route_key in api_routes:
                                colliding_story = api_routes[route_key]
                                passed = False
                                err_msg = f"API route conflict: {route_key} in {s_key} collides with {colliding_story}"
                                errors.append(err_msg)
                                failed_stories.add(s_key)
                                failed_stories.add(colliding_story)
                            else:
                                api_routes[route_key] = s_key
                    except Exception as e:
                        logger.error("CrossStoryValidator: Failed to read %s: %s", py_file, e)

            # Scan database tables and check duplicate definitions
            db_dir = story_dir / "database"
            if db_dir.exists():
                for sql_file in db_dir.glob("*.sql"):
                    try:
                        content = sql_file.read_text(encoding="utf-8")
                        # Match CREATE TABLE statement
                        tables = re.findall(r"CREATE\s+TABLE\s+(\w+)", content, re.IGNORECASE)
                        for tbl in tables:
                            tbl_lower = tbl.lower()
                            if tbl_lower in database_tables:
                                passed = False
                                err_msg = f"Database Table collision: table '{tbl_lower}' in story {s_key} was already defined."
                                errors.append(err_msg)
                                failed_stories.add(s_key)
                            else:
                                database_tables.add(tbl_lower)
                    except Exception as e:
                        logger.error("CrossStoryValidator: Failed to read %s: %s", sql_file, e)

        return {
            "passed": passed,
            "errors": errors,
            "failed_stories": list(failed_stories)
        }
