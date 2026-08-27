"""NFR Analyzer — uses an LLM to identify Non-Functional Requirements
such as performance, security, scalability and observability needs."""

from typing import Any, Dict, List

from app.utils.json_utils import safe_extract_json
from app.utils.logger import get_logger

logger = get_logger(__name__)

_SYSTEM = """You are a senior architect specialising in quality attributes.
Identify the Non-Functional Requirements (NFRs) for the described system.

Return ONLY a single valid JSON object — no prose, no markdown fences.

Required schema:
{
  "nfrs": [
    {
      "category": "<performance | security | scalability | reliability | maintainability | observability | accessibility>",
      "requirement": "<clear NFR statement>",
      "rationale": "<why this matters for this system>",
      "priority": "<high | medium | low>"
    }
  ]
}
"""


class NFRAnalyzer:
    """Use an LLM to identify Non-Functional Requirements."""

    def __init__(self, llm=None) -> None:
        self._llm = llm

    def analyze(
        self, project_config: Dict[str, Any], features: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Identify NFRs for the project.

        Args:
            project_config: Structured project config.
            features:       Feature list from FeatureIdentifier.

        Returns:
            Dict with 'nfrs' key.
        """
        features_text = "\n".join(f"- {f['name']}: {f.get('description', '')}" for f in features)
        user_prompt = (
            f"Project: {project_config.get('project_name')}\n"
            f"Tech stack: {project_config.get('tech_stack')}\n\n"
            f"Features:\n{features_text}"
        )

        logger.info("NFRAnalyzer: calling LLM")
        raw = self._llm.complete(_SYSTEM, user_prompt)
        result = safe_extract_json(raw, fallback={"nfrs": []})
        result.setdefault("nfrs", [])
        return result
