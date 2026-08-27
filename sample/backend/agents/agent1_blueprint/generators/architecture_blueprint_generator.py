"""Architecture Blueprint Generator — uses an LLM to synthesise all analysis
results into a complete, human-readable architecture blueprint and the
structured MasterBlueprint.json payload."""

from typing import Any, Dict, List

from app.utils.json_utils import safe_extract_json
from app.utils.logger import get_logger

logger = get_logger(__name__)

_SYSTEM_STRUCTURED = """You are a principal software architect.
Synthesise the provided analysis into a complete architecture blueprint.

Return ONLY a single valid JSON object — no prose, no markdown fences.

Required schema:
{
  "project_name": "<project name>",
  "summary": "<2-3 sentence architectural summary>",
  "modules": [
    {
      "name": "<module name>",
      "layer": "<backend | frontend | shared>",
      "description": "<what this module does>",
      "responsibilities": ["<responsibility>", ...]
    }
  ],
  "components": [
    {
      "name": "<component name>",
      "type": "<service | gateway | store | queue | cache | frontend>",
      "role": "<role description>",
      "technology": "<specific technology used>"
    }
  ],
  "integration_points": [
    {
      "name": "<integration name>",
      "type": "<internal | external | third-party>",
      "protocol": "<REST | gRPC | WebSocket | event | email | sms>",
      "description": "<integration description>"
    }
  ],
  "data_flow": "<1-2 sentences describing main data flows>",
  "security_approach": "<1-2 sentences on auth/authz approach>",
  "deployment_approach": "<1-2 sentences on how this gets deployed>"
}
"""

_SYSTEM_HUMAN_READABLE = """You are a technical writer and architect.
Write a clear, human-readable architecture blueprint document from the provided structured blueprint JSON.

The document must include:
1. Overview section
2. Modules and their responsibilities
3. Core components and technologies
4. Integration points
5. Data flow summary
6. Security approach
7. Deployment approach

Use plain text with section headers (no markdown). Be concise and precise.
"""


class ArchitectureBlueprintGenerator:
    """Use an LLM to generate both the structured MasterBlueprint and a human-readable text."""

    def __init__(self, llm=None) -> None:
        self._llm = llm

    def generate(
        self,
        project_config: Dict[str, Any],
        stories: List[Dict[str, Any]],
        features: List[Dict[str, Any]],
        modules: List[Dict[str, Any]],
        data_model: Dict[str, Any],
        nfrs: Dict[str, Any],
        project_overview: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate the MasterBlueprint.

        Args:
            project_config:   Structured config from ConfigAnalyzer.
            stories:          Normalised stories.
            features:         Identified features.
            modules:          Identified modules.
            data_model:       Domain data model.
            nfrs:             Non-functional requirements.
            project_overview: High-level project overview.

        Returns:
            MasterBlueprint dict including a 'text_blueprint' key.
        """
        context = self._build_context(project_config, stories, features, modules, data_model, nfrs, project_overview)

        logger.info("ArchitectureBlueprintGenerator: generating structured blueprint")
        raw_structured = self._llm.complete(_SYSTEM_STRUCTURED, context)
        blueprint = safe_extract_json(raw_structured, fallback={})

        # Ensure required keys
        blueprint.setdefault("project_name", project_config.get("project_name", "Generated Platform"))
        blueprint.setdefault("summary", "")
        blueprint.setdefault("modules", modules)
        blueprint.setdefault("components", [])
        blueprint.setdefault("integration_points", [])
        blueprint.setdefault("data_flow", "")
        blueprint.setdefault("security_approach", "")
        blueprint.setdefault("deployment_approach", "")

        logger.info("ArchitectureBlueprintGenerator: generating human-readable blueprint")
        import json
        blueprint_json_str = json.dumps(blueprint, indent=2)
        text_blueprint = self._llm.complete(_SYSTEM_HUMAN_READABLE, blueprint_json_str)
        blueprint["text_blueprint"] = text_blueprint.strip()

        return blueprint

    def _build_context(
        self,
        project_config: Dict[str, Any],
        stories: List[Dict[str, Any]],
        features: List[Dict[str, Any]],
        modules: List[Dict[str, Any]],
        data_model: Dict[str, Any],
        nfrs: Dict[str, Any],
        project_overview: Dict[str, Any],
    ) -> str:
        import json
        # Keep context concise to stay within free-tier token limits.
        # Send summaries rather than full nested JSON for large lists.
        story_lines = "\n".join(f"- [{s['id']}] {s['title']}" for s in stories)
        feature_lines = "\n".join(
            f"- {f['name']}: {f.get('description', '')[:100]}" for f in features
        )
        module_lines = "\n".join(
            f"- [{m.get('layer','?')}] {m['name']}: {m.get('description','')[:100]}"
            for m in modules
        )
        entity_names = [e.get("name", "") for e in data_model.get("entities", [])]
        nfr_lines = "\n".join(
            f"- [{n.get('category','?')}] {n.get('requirement','')[:80]}"
            for n in nfrs.get("nfrs", [])
        )
        return (
            f"PROJECT: {project_config.get('project_name')}\n"
            f"TECH STACK: {json.dumps(project_config.get('tech_stack', {}))}\n"
            f"OVERVIEW: {project_overview.get('project_overview', '')[:300]}\n\n"
            f"STORIES:\n{story_lines}\n\n"
            f"FEATURES:\n{feature_lines}\n\n"
            f"MODULES:\n{module_lines}\n\n"
            f"ENTITIES: {', '.join(entity_names)}\n\n"
            f"NFRs:\n{nfr_lines}"
        )
