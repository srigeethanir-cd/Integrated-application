from typing import Any, Dict, List

class DependencyBlueprintGenerator:
    """Generate dependency relationships between modules and external services."""

    def generate(self, project_config: Dict[str, Any], stories: List[Dict[str, Any]]) -> Dict[str, Any]:
        project_name = project_config.get("project_name", "generated_project")
        dependencies = []

        # Find modules/feature groups
        feature_groups = set()
        for story in stories:
            fg = story.get("feature_group")
            if fg:
                feature_groups.add(fg)

        if not feature_groups:
            feature_groups.add("core")

        # Create relationships
        for fg in sorted(feature_groups):
            # Module depends on database
            dependencies.append({
                "source": f"backend/{fg}",
                "target": "database",
                "type": "database_connection",
                "required": True
            })
            # Module depends on shared logging & utilities
            dependencies.append({
                "source": f"backend/{fg}",
                "target": "shared",
                "type": "shared_utility_import",
                "required": True
            })
            # If not authentication, it depends on authentication module
            if fg != "authentication" and "authentication" in feature_groups:
                dependencies.append({
                    "source": f"backend/{fg}",
                    "target": "backend/authentication",
                    "type": "auth_middleware_import",
                    "required": True
                })

        return {
            "project_name": project_name,
            "dependencies": dependencies
        }
