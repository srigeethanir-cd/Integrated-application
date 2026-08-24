import logging
from typing import Dict, Any, List, Set
from sqlalchemy.orm import Session
from app.models import DependencyGraphRecord

logger = logging.getLogger(__name__)

class StoryDependencyResolver:
    """Analyzes requirements to resolve story dependencies and stores them in PostgreSQL."""

    def __init__(self, db: Session, project_id: str):
        self.db = db
        self.project_id = project_id

    def resolve_dependencies(self, stories: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze story dependencies and save to database."""
        nodes = []
        links = []
        dependency_map: Dict[str, List[str]] = {}

        # 1. Register story nodes
        for story in stories:
            s_key = story.get("story_key", "US001").upper()
            nodes.append({"id": s_key, "label": story.get("title", ""), "type": "story"})
            dependency_map[s_key] = []

        # 2. Rule-based dependency resolution
        for s1 in stories:
            k1 = s1.get("story_key", "US001").upper()
            t1 = s1.get("title", "").lower()
            d1 = s1.get("description", "").lower() if s1.get("description") else ""

            for s2 in stories:
                k2 = s2.get("story_key", "US001").upper()
                if k1 == k2:
                    continue
                t2 = s2.get("title", "").lower()
                d2 = s2.get("description", "").lower() if s2.get("description") else ""

                if ("login" in t1 or "profile" in t1 or "auth" in t1 or "logout" in t1) and ("register" in t2 or "create user" in t2 or "signup" in t2 or "user account" in t2):
                    dependency_map[k1].append(k2)
                    links.append({"source": k2, "target": k1, "type": "required_by"})
                
                if k2.lower() in t1 or k2.lower() in d1:
                    dependency_map[k1].append(k2)
                    links.append({"source": k2, "target": k1, "type": "explicit"})

        # 3. Compute topological sort execution order
        execution_order = self._topological_sort(dependency_map)

        graph_data = {"nodes": nodes, "links": links}
        report_data = {
            "resolved_at": datetime_now_iso(),
            "dependencies": {k: list(set(v)) for k, v in dependency_map.items()},
            "critical_path": [k for k in execution_order if dependency_map.get(k)]
        }

        # 4. Persist to PostgreSQL DependencyGraphRecord
        try:
            # Clear existing record if any
            self.db.query(DependencyGraphRecord).filter_by(project_id=self.project_id).delete()
            self.db.commit()
        except Exception:
            self.db.rollback()

        graph_rec = DependencyGraphRecord(
            project_id=self.project_id,
            dependency_graph_json=graph_data,
            execution_order_json=execution_order
        )
        self.db.add(graph_rec)
        self.db.commit()

        logger.info("DependencyResolver: Resolved and saved dependency graph to PostgreSQL.")

        return {
            "dependency_graph": graph_data,
            "execution_order": execution_order,
            "dependency_report": report_data
        }

    def _topological_sort(self, dependency_map: Dict[str, List[str]]) -> List[str]:
        visited: Set[str] = set()
        temp: Set[str] = set()
        order: List[str] = []

        def visit(node: str):
            if node in temp:
                return
            if node not in visited:
                temp.add(node)
                for dep in dependency_map.get(node, []):
                    if dep in dependency_map:
                        visit(dep)
                temp.remove(node)
                visited.add(node)
                order.append(node)

        for node in dependency_map:
            visit(node)

        return order

def datetime_now_iso():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()
