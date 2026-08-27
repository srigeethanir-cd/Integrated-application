import json
from typing import Any, Dict, Optional

class ConfigLoader:
    """Load and normalize user configuration files or inputs."""

    def load_config_from_dict(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize tech stack keys from dict."""
        tech_stack = config_data.get("tech_stack", {})
        return {
            "project_name": config_data.get("project_name", "Generated Project"),
            "tech_stack": {
                "backend": tech_stack.get("backend", "python").lower(),
                "frontend": tech_stack.get("frontend", "react").lower(),
                "database": tech_stack.get("database", "postgresql").lower(),
                "infrastructure": tech_stack.get("infrastructure", "docker").lower(),
            },
            "features": config_data.get("features", []),
        }

    def load_config_from_json(self, json_str: str) -> Optional[Dict[str, Any]]:
        """Parse configuration from JSON string."""
        try:
            data = json.loads(json_str)
            return self.load_config_from_dict(data)
        except json.JSONDecodeError:
            return None
