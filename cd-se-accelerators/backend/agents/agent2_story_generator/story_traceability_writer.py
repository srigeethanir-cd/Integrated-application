"""Story Traceability Writer for Agent 2.

Generates and maintains traceability.json establishing traceability links across all software layers.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class StoryTraceabilityWriter:
    """Generates traceability.json establishing full traceability links."""

    def write_traceability(
        self,
        story_key: str,
        epic_key: str,
        story_workspace_path: str,
        generated_files: List[str],
        api_endpoint: str = "/api/v1/resource",
        db_table: str = "resources",
    ) -> Dict[str, Any]:
        """Write traceability.json into story workspace."""
        traceability_data = {
            "story_key": story_key,
            "epic_key": epic_key,
            "traceability_matrix": {
                "requirement_id": f"REQ-{story_key}",
                "epic_id": epic_key,
                "user_story_id": story_key,
                "frontend_components": [f for f in generated_files if "frontend" in f or "Page" in f or "Component" in f],
                "backend_services": [f for f in generated_files if "service" in f or "backend" in f],
                "api_endpoints": [api_endpoint],
                "database_tables": [db_table],
                "tests": [f for f in generated_files if "test" in f],
                "all_generated_files": generated_files,
            },
        }

        ws_root = Path(story_workspace_path)
        trace_path = ws_root / "traceability.json"
        with open(trace_path, "w", encoding="utf-8") as f:
            json.dump(traceability_data, f, indent=2)

        logger.info("StoryTraceabilityWriter: Saved traceability.json for story %s", story_key)
        return traceability_data
