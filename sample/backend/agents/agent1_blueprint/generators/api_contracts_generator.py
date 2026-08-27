from typing import Any, Dict, List

class APIContractsGenerator:
    """Generate API contracts based on modules and user stories."""

    def generate(self, project_config: Dict[str, Any], stories: List[Dict[str, Any]]) -> Dict[str, Any]:
        project_name = project_config.get("project_name", "generated_project")
        contracts = []

        # Find modules/feature groups
        feature_groups = set()
        for story in stories:
            fg = story.get("feature_group")
            if fg:
                feature_groups.add(fg)

        if not feature_groups:
            feature_groups.add("core")

        for fg in sorted(feature_groups):
            endpoints = [
                {
                    "path": f"/api/v1/{fg}",
                    "method": "GET",
                    "description": f"Retrieve list of {fg} items",
                    "parameters": [
                        {"name": "page", "in": "query", "type": "integer", "required": False},
                        {"name": "page_size", "in": "query", "type": "integer", "required": False}
                    ],
                    "responses": {
                        "200": {"description": "Success", "schema": {"type": "array", "items": {"type": "object"}}}
                    }
                },
                {
                    "path": f"/api/v1/{fg}",
                    "method": "POST",
                    "description": f"Create a new {fg} item",
                    "request_body": {
                        "required": True,
                        "schema": {"type": "object", "properties": {"name": {"type": "string"}}}
                    },
                    "responses": {
                        "201": {"description": "Created", "schema": {"type": "object"}}
                    }
                },
                {
                    "path": f"/api/v1/{fg}/{{id}}",
                    "method": "GET",
                    "description": f"Retrieve a single {fg} item by ID",
                    "parameters": [
                        {"name": "id", "in": "path", "type": "string", "required": True}
                    ],
                    "responses": {
                        "200": {"description": "Success", "schema": {"type": "object"}},
                        "404": {"description": "Not Found"}
                    }
                }
            ]
            contracts.append({
                "module": fg.replace("_", " ").title(),
                "endpoints": endpoints
            })

        return {
            "project_name": project_name,
            "contracts": contracts
        }
