"""Blueprint Generator module for Agent 1.

Produces MasterBlueprint.json and ProjectManifest.json artifacts.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

from agents.agent1_blueprint.requirement_analysis import RequirementSpec
from agents.agent1_blueprint.story_generator import GeneratedStory

logger = logging.getLogger(__name__)


class BlueprintGenerator:
    """Produces MasterBlueprint.json and ProjectManifest.json containing full architectural specifications."""

    def generate_master_blueprint(
        self,
        req_spec: RequirementSpec,
        stories: List[GeneratedStory],
    ) -> Dict[str, Any]:
        """Generate MasterBlueprint.json dictionary."""
        api_blueprints = []
        db_blueprints = []
        modules = []
        seen_modules = set()

        for s in stories:
            api_blueprints.append({
                "story_key": s.story_key,
                "endpoint": s.api_endpoint,
                "method": "GET/POST/PUT/DELETE",
                "db_table": s.db_table,
            })
            db_blueprints.append({
                "table_name": s.db_table,
                "columns": [
                    {"name": "id", "type": "String(36)", "primary_key": True},
                    {"name": "created_at", "type": "DateTime", "nullable": False},
                    {"name": "updated_at", "type": "DateTime", "nullable": False},
                ],
            })
            mod_name = s.db_table or f"module_{s.story_key.lower()}"
            if mod_name not in seen_modules:
                seen_modules.add(mod_name)
                modules.append({
                    "name": mod_name,
                    "description": f"Module handling {s.title} and related services.",
                    "endpoints": [s.api_endpoint],
                })

        return {
            "project_name": req_spec.project_name,
            "tech_stack": req_spec.tech_stack,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "architecture": {
                "backend": "FastAPI Async / SQLAlchemy 2.0 / Alembic",
                "frontend": "React TypeScript / React Router v6 / Tailwind CSS",
                "database": "PostgreSQL 16 / SQLite Fallback",
            },
            "modules": modules,
            "api_contracts": api_blueprints,
            "database_schemas": db_blueprints,
            "non_functional_requirements": req_spec.nfrs,
        }

    def generate_project_manifest(
        self,
        req_spec: RequirementSpec,
        master_blueprint: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate ProjectManifest.json dictionary."""
        return {
            "name": req_spec.project_name,
            "version": "0.1.0",
            "tech_stack": req_spec.tech_stack,
            "manifest_version": "1.0",
            "blueprint_summary": {
                "api_count": len(master_blueprint.get("api_contracts", [])),
                "table_count": len(master_blueprint.get("database_schemas", [])),
            },
        }
