"""Feature Identifier — uses an LLM to group normalised stories into cohesive
feature sets with descriptions and acceptance notes."""

from typing import Any, Dict, List

from app.utils.json_utils import safe_extract_json
from app.utils.logger import get_logger

logger = get_logger(__name__)

_SYSTEM = """You are a product architect.
Group the provided user stories into cohesive product features.

Return ONLY a single valid JSON object — no prose, no markdown fences.

Required schema:
{
  "features": [
    {
      "name": "<feature name>",
      "description": "<what this feature does>",
      "stories": ["<story id 1>", "<story id 2>", ...],
      "user_roles": ["<role 1>", ...],
      "acceptance_notes": "<high-level acceptance notes for the feature>"
    }
  ]
}
"""


class FeatureIdentifier:
    """Use an LLM to identify and group features from normalised stories."""

    def __init__(self, llm=None) -> None:
        self._llm = llm

    def identify(
        self, stories: List[Dict[str, Any]], project_config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Return a list of feature dicts derived from the stories.

        Args:
            stories:        Normalised stories from StoryAnalyzer.
            project_config: Structured project config.

        Returns:
            List of feature dicts.
        """
        stories_text = "\n".join(
            f"- [{s['id']}] {s['title']} (group: {s.get('feature_group', 'core')})"
            for s in stories
        )
        user_prompt = (
            f"Project: {project_config.get('project_name')}\n\n"
            f"Stories:\n{stories_text}"
        )

        logger.info("FeatureIdentifier: calling LLM")
        raw = self._llm.complete(_SYSTEM, user_prompt)
        result = safe_extract_json(raw, fallback={"features": []})
        return result.get("features", [])
