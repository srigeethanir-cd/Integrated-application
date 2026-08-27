"""Shared Components Generator — uses an LLM to identify cross-cutting
components that are reused across modules and layers."""

from typing import Any, Dict, List

from app.utils.json_utils import safe_extract_json
from app.utils.logger import get_logger

logger = get_logger(__name__)

_SYSTEM = """You are a software architect specialising in reusable component design.
Identify shared / cross-cutting components from the provided modules and features.

Return ONLY a single valid JSON object — no prose, no markdown fences.

Required schema:
{
  "shared_components": [
    {
      "name": "<component name>",
      "owner": "<shared | platform | infrastructure>",
      "description": "<what this component does>",
      "used_by": ["<module name 1>", ...],
      "type": "<utility | middleware | service | library | config>"
    }
  ]
}
"""


class SharedComponentsGenerator:
    """Use an LLM to detect shared components across modules."""

    def __init__(self, llm=None) -> None:
        self._llm = llm

    def detect(
        self,
        project_config: Dict[str, Any],
        modules: List[Dict[str, Any]],
        features: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Return a list of shared component dicts.

        Args:
            project_config: Structured project config.
            modules:        Identified modules.
            features:       Identified features.

        Returns:
            List of shared component dicts.
        """
        import json

        user_prompt = (
            f"Project: {project_config.get('project_name')}\n"
            f"Tech stack: {project_config.get('tech_stack')}\n\n"
            f"Modules:\n{json.dumps(modules, indent=2)}\n\n"
            f"Features:\n{json.dumps(features, indent=2)}"
        )

        logger.info("SharedComponentsGenerator: calling LLM")
        raw = self._llm.complete(_SYSTEM, user_prompt)
        result = safe_extract_json(raw, fallback={"shared_components": []})
        return result.get("shared_components", [])
