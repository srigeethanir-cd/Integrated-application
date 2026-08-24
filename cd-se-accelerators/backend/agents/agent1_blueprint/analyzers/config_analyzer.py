"""Config Analyzer — uses an LLM to extract a structured project configuration
from a natural-language tech-stack description and a set of user stories."""

from typing import Any, Dict, List

from app.utils.json_utils import safe_extract_json
from app.utils.logger import get_logger

logger = get_logger(__name__)

_SYSTEM = """You are a senior software architect.
Your job is to extract a structured project configuration from a natural-language
technology description and a list of user stories.

Return ONLY a single valid JSON object — no prose, no markdown fences.

Required schema:
{
  "project_name": "<short, title-cased name inferred from the stories>",
  "tech_stack": {
    "backend":        "<primary backend framework or language>",
    "frontend":       "<primary frontend framework or library>",
    "database":       "<primary database technology>",
    "infrastructure": "<primary deployment or container technology>"
  },
  "features": ["<feature 1>", "<feature 2>", ...],
  "nlp_normalized": {
    "raw_tech_input": "<the original tech string>",
    "inferred_patterns": ["<pattern 1>", "<pattern 2>", ...]
  }
}
"""


class ConfigAnalyzer:
    """Use an LLM to parse a natural-language tech-stack string into a project config."""

    def __init__(self, llm=None) -> None:
        self._llm = llm  # injected by Agent1; lazy-init avoids import-time failures

    def infer_project_config(
        self, tech_stack: str, stories: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Ask the LLM to extract the project configuration.

        Args:
            tech_stack: Free-text description of the technology stack.
            stories:    Normalised list of user story dicts.

        Returns:
            Structured project config dict.
        """
        story_titles = [s.get("title", "") for s in stories[:10]]
        user_prompt = (
            f"Tech stack description:\n{tech_stack}\n\n"
            f"User story titles (first {len(story_titles)}):\n"
            + "\n".join(f"- {t}" for t in story_titles)
        )

        logger.info("ConfigAnalyzer: calling LLM to infer project config")
        raw = self._llm.complete(_SYSTEM, user_prompt)
        config = safe_extract_json(raw, fallback={})

        # Ensure required keys exist with safe defaults
        config.setdefault("project_name", "Generated Platform")
        config.setdefault("tech_stack", {
            "backend": "python", "frontend": "react",
            "database": "postgresql", "infrastructure": "docker",
        })
        config.setdefault("features", [])
        config.setdefault("nlp_normalized", {"raw_tech_input": tech_stack, "inferred_patterns": []})

        logger.info("ConfigAnalyzer: project_name=%s", config["project_name"])
        return config
