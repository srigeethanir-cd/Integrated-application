"""Project Analyzer — uses an LLM to produce a high-level project overview
including goals, scope, constraints and success metrics."""

from typing import Any, Dict, List

from app.utils.json_utils import safe_extract_json
from app.utils.logger import get_logger

logger = get_logger(__name__)

_SYSTEM = """You are a senior solution architect.
Produce a concise high-level project overview from the provided configuration and stories.

Return ONLY a single valid JSON object — no prose, no markdown fences.

Required schema:
{
  "project_overview": "<2-3 sentence description of the system being built>",
  "primary_goals": ["<goal 1>", "<goal 2>", ...],
  "scope": {
    "in_scope": ["<item 1>", ...],
    "out_of_scope": ["<item 1>", ...]
  },
  "constraints": ["<constraint 1>", ...],
  "success_metrics": ["<metric 1>", ...]
}
"""


class ProjectAnalyzer:
    """Use an LLM to derive a high-level project overview."""

    def __init__(self, llm=None) -> None:
        self._llm = llm

    def analyze(
        self, project_config: Dict[str, Any], stories: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Ask the LLM to produce a project overview.

        Args:
            project_config: Structured config from ConfigAnalyzer.
            stories:        Normalised stories from StoryAnalyzer.

        Returns:
            Project overview dict.
        """
        story_titles = [s.get("title", "") for s in stories]
        user_prompt = (
            f"Project name: {project_config.get('project_name')}\n"
            f"Tech stack: {project_config.get('tech_stack')}\n"
            f"Features: {project_config.get('features')}\n\n"
            f"User stories:\n" + "\n".join(f"- {t}" for t in story_titles)
        )

        logger.info("ProjectAnalyzer: calling LLM for project overview")
        raw = self._llm.complete(_SYSTEM, user_prompt)
        result = safe_extract_json(raw, fallback={})

        result.setdefault("project_overview", "")
        result.setdefault("primary_goals", [])
        result.setdefault("scope", {"in_scope": [], "out_of_scope": []})
        result.setdefault("constraints", [])
        result.setdefault("success_metrics", [])
        return result
