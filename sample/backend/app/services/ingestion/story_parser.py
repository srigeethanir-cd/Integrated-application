import json
from typing import Any, Dict, List, Optional

class StoryParser:
    """Parse raw epics and user stories from structured payloads or JSON inputs."""

    def parse_stories(self, stories_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize stories and assign fallback fields."""
        parsed_stories = []
        for index, story in enumerate(stories_data):
            story_id = story.get("id") or f"US-{index + 1}"
            title = story.get("title") or "Untitled User Story"
            description = story.get("description") or ""
            ac = story.get("acceptance_criteria") or []
            if isinstance(ac, str):
                ac = [item.strip() for item in ac.split(",") if item.strip()]

            parsed_stories.append({
                "id": story_id,
                "title": title,
                "description": description,
                "acceptance_criteria": ac,
                "epic_id": story.get("epic_id")
            })
        return parsed_stories

    def parse_from_json(self, json_str: str) -> Optional[List[Dict[str, Any]]]:
        """Parse stories list from JSON string."""
        try:
            data = json.loads(json_str)
            if isinstance(data, list):
                return self.parse_stories(data)
            elif isinstance(data, dict) and "stories" in data:
                return self.parse_stories(data["stories"])
            return None
        except json.JSONDecodeError:
            return None
