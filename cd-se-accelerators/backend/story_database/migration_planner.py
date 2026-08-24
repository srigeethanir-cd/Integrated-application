import logging
from typing import Dict, Any, List, Set
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class DatabaseMigrationPlanner:
    """Coordinates database schema migrations, checks table dependencies and generates plans in PostgreSQL."""

    def __init__(self, db: Session, project_id: str):
        self.db = db
        self.project_id = project_id

    def plan_migrations(self, migrations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyzes migration files/schemas, determines dependencies."""
        nodes = []
        links = []
        dep_map: Dict[str, List[str]] = {}

        # 1. Register tables
        for m in migrations:
            tbl = m.get("table_name", "").lower()
            if not tbl:
                continue
            nodes.append({"id": tbl, "story_key": m.get("story_key", "US101"), "type": "table"})
            dep_map[tbl] = []

        # 2. Analyze foreign key dependencies
        for m in migrations:
            tbl = m.get("table_name", "").lower()
            fks = m.get("foreign_keys", [])
            for fk in fks:
                fk_lower = fk.lower()
                if fk_lower in dep_map and fk_lower != tbl:
                    dep_map[tbl].append(fk_lower)
                    links.append({"source": fk_lower, "target": tbl, "relationship": "references"})

        # 3. Compute topological order of execution
        execution_order = self._topological_sort(dep_map)

        plan = []
        for tbl in execution_order:
            orig = next((m for m in migrations if m.get("table_name", "").lower() == tbl), None)
            if orig:
                plan.append({
                    "table_name": tbl,
                    "story_key": orig.get("story_key"),
                    "action": "CREATE TABLE",
                    "fields": orig.get("fields", []),
                    "dependencies": dep_map[tbl]
                })

        logger.info("MigrationPlanner: Computed database migration plan for %d tables.", len(plan))
        return {
            "migration_plan": plan,
            "dependency_graph": {"nodes": nodes, "links": links},
            "execution_order": execution_order
        }

    def _topological_sort(self, dep_map: Dict[str, List[str]]) -> List[str]:
        visited: Set[str] = set()
        temp: Set[str] = set()
        order: List[str] = []

        def visit(node: str):
            if node in temp:
                return
            if node not in visited:
                temp.add(node)
                for dep in dep_map.get(node, []):
                    if dep in dep_map:
                        visit(dep)
                temp.remove(node)
                visited.add(node)
                order.append(node)

        for node in dep_map:
            visit(node)
        return order
