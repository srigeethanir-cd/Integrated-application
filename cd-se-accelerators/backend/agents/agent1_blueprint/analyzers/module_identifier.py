"""Module Identifier — uses an LLM to decompose identified features into
concrete backend / frontend modules with responsibilities and interfaces."""

from typing import Any, Dict, List

from app.utils.json_utils import safe_extract_json
from app.utils.logger import get_logger

logger = get_logger(__name__)

_SYSTEM = """You are a senior software architect.
Decompose the provided product features into concrete software modules.

Return ONLY a single valid JSON object — no prose, no markdown fences.

Required schema:
{
  "modules": [
    {
      "name": "<module name>",
      "layer": "<backend | frontend | shared>",
      "description": "<what this module does>",
      "responsibilities": ["<responsibility 1>", ...],
      "exposes": ["<API endpoint or component name>", ...],
      "depends_on": ["<other module name>", ...]
    }
  ]
}
"""


class ModuleIdentifier:
    """Use an LLM to decompose features into software modules."""

    def __init__(self, llm=None) -> None:
        self._llm = llm

    def identify(
        self, features: List[Dict[str, Any]], project_config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Return a list of module dicts.

        Args:
            features:       Feature list from FeatureIdentifier.
            project_config: Structured project config.

        Returns:
            List of module dicts.
        """
        features_text = "\n".join(
            f"- {f['name']}: {f.get('description', '')}" for f in features
        )
        user_prompt = (
            f"Project: {project_config.get('project_name')}\n"
            f"Tech stack: {project_config.get('tech_stack')}\n\n"
            f"Features:\n{features_text}"
        )

        logger.info("ModuleIdentifier: calling LLM")
        raw = self._llm.complete(_SYSTEM, user_prompt)
        result = safe_extract_json(raw, fallback={"modules": []})
        return result.get("modules", [])
