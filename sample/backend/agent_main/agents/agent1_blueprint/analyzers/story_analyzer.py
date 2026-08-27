"""Story Analyzer — uses an LLM to deeply analyse raw user stories and return
a rich normalised structure for all downstream generators."""

from typing import Any, Dict, List

from app.utils.json_utils import safe_extract_json
from app.utils.logger import get_logger

logger = get_logger(__name__)

_SYSTEM = """You are an expert Business Analyst and Requirements Engineer.
Analyse the provided user stories and return a deeply normalised structure.

Return ONLY a single valid JSON object — no prose, no markdown fences.

Required schema:
{
  "stories": [
    {
      "id": "<story id>",
      "title": "<story title>",
      "description": "<full description>",
      "acceptance_criteria": ["<criterion 1>", ...],
      "actors": ["<actor 1>", ...],
      "feature_group": "<logical feature group name, e.g. authentication>",
      "priority": "<high | medium | low>",
      "complexity": "<simple | moderate | complex>",
      "dependencies": ["<story id or feature this depends on>", ...],
      "keywords": ["<keyword 1>", ...]
    }
  ],
  "summary": "<2-3 sentence overview of all the stories together>"
}
"""


class StoryAnalyzer:
    """Use an LLM to analyse and normalise raw user stories."""

    def __init__(self, llm=None) -> None:
        self._llm = llm

    def analyze_stories(self, stories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyse and enrich all stories via LLM.

        Args:
            stories: Raw user story dicts from the caller.

        Returns:
            List of normalised story dicts.
        """
        if not stories:
            return []

        stories_text = "\n\n".join(
            f"ID: {s.get('id', f'STORY-{i+1}')}\n"
            f"Title: {s.get('title', 'Untitled')}\n"
            f"Description: {s.get('description', '')}\n"
            f"Acceptance Criteria: {s.get('acceptance_criteria', [])}"
            for i, s in enumerate(stories)
        )

        user_prompt = f"Analyse the following user stories:\n\n{stories_text}"

        logger.info("StoryAnalyzer: calling LLM for %d stories", len(stories))
        raw = self._llm.complete(_SYSTEM, user_prompt)
        result = safe_extract_json(raw, fallback={"stories": []})

        normalised = result.get("stories", [])

        # Safety: ensure every story has the required fields
        for i, story in enumerate(normalised):
            story.setdefault("id", stories[i].get("id", f"STORY-{i+1}") if i < len(stories) else f"STORY-{i+1}")
            story.setdefault("title", "Untitled")
            story.setdefault("description", "")
            story.setdefault("acceptance_criteria", [])
            story.setdefault("actors", [])
            story.setdefault("feature_group", "core_workflow")
            story.setdefault("priority", "medium")
            story.setdefault("complexity", "moderate")
            story.setdefault("dependencies", [])
            story.setdefault("keywords", [])

        logger.info("StoryAnalyzer: normalised %d stories", len(normalised))
        return normalised
