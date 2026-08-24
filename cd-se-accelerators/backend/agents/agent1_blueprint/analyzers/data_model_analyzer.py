"""Data Model Analyzer — uses an LLM to derive the domain data model
(entities, attributes, relationships) from features and stories."""

from typing import Any, Dict, List

from app.utils.json_utils import safe_extract_json
from app.utils.logger import get_logger

logger = get_logger(__name__)

_SYSTEM = """You are a database architect.
Derive the domain data model from the provided features and user stories.

Return ONLY a single valid JSON object — no prose, no markdown fences.

Required schema:
{
  "entities": [
    {
      "name": "<entity name, PascalCase>",
      "description": "<what this entity represents>",
      "attributes": [
        {
          "name": "<attribute name>",
          "type": "<data type, e.g. string, integer, boolean, datetime>",
          "required": true,
          "description": "<what this attribute holds>"
        }
      ],
      "relationships": [
        {
          "entity": "<related entity name>",
          "type": "<one_to_one | one_to_many | many_to_many>",
          "description": "<relationship description>"
        }
      ]
    }
  ]
}
"""


class DataModelAnalyzer:
    """Use an LLM to derive the domain data model."""

    def __init__(self, llm=None) -> None:
        self._llm = llm

    def analyze(
        self,
        features: List[Dict[str, Any]],
        stories: List[Dict[str, Any]],
        project_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Return the domain data model.

        Args:
            features:       Feature list from FeatureIdentifier.
            stories:        Normalised stories from StoryAnalyzer.
            project_config: Structured project config.

        Returns:
            Dict with 'entities' key.
        """
        features_text = "\n".join(f"- {f['name']}: {f.get('description', '')}" for f in features)
        story_titles = "\n".join(f"- {s['title']}" for s in stories)
        user_prompt = (
            f"Project: {project_config.get('project_name')}\n"
            f"Database: {project_config.get('tech_stack', {}).get('database', 'postgresql')}\n\n"
            f"Features:\n{features_text}\n\n"
            f"Stories:\n{story_titles}"
        )

        logger.info("DataModelAnalyzer: calling LLM")
        raw = self._llm.complete(_SYSTEM, user_prompt)
        result = safe_extract_json(raw, fallback={"entities": []})
        result.setdefault("entities", [])
        return result
