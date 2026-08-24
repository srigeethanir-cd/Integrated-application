from typing import Any, Dict, List, Tuple

class InputValidator:
    """Validate configuration inputs and user story requirements."""

    def validate_config(self, config_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        errors = []
        if not config_data.get("project_name"):
            errors.append("Missing project_name.")
        
        tech_stack = config_data.get("tech_stack", {})
        if not isinstance(tech_stack, dict):
            errors.append("tech_stack must be a dictionary.")
        else:
            required_keys = ["backend", "frontend", "database"]
            for key in required_keys:
                if not tech_stack.get(key):
                    errors.append(f"Missing tech_stack key: {key}")

        return len(errors) == 0, errors

    def validate_stories(self, stories: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
        errors = []
        if not isinstance(stories, list):
            return False, ["Stories payload must be a list."]

        for index, story in enumerate(stories):
            story_id = story.get("id")
            title = story.get("title")
            desc = story.get("description")

            if not story_id:
                errors.append(f"Story at index {index} is missing 'id'.")
            if not title:
                errors.append(f"Story '{story_id or index}' is missing 'title'.")
            if not desc:
                errors.append(f"Story '{story_id or index}' is missing 'description'.")

        return len(errors) == 0, errors
