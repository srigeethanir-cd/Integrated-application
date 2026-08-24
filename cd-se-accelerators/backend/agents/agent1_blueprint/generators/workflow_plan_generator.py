"""Workflow Plan Generator — uses an LLM to produce a phased implementation
plan and a human-readable version of it."""

from typing import Any, Dict, List

from app.utils.json_utils import safe_extract_json
from app.utils.logger import get_logger

logger = get_logger(__name__)

_SYSTEM_STRUCTURED = """You are an engineering delivery manager.
Create a detailed, phased implementation plan for the described project.

Return ONLY a single valid JSON object — no prose, no markdown fences.

Required schema:
{
  "project_name": "<project name>",
  "phases": [
    {
      "phase": "<phase name>",
      "order": 1,
      "goal": "<what this phase achieves>",
      "deliverables": ["<deliverable 1>", ...],
      "stories_covered": ["<story id 1>", ...],
      "estimated_effort": "<e.g. 1-2 weeks>",
      "dependencies": ["<phase name this depends on, or empty>"]
    }
  ],
  "milestones": [
    {
      "name": "<milestone name>",
      "description": "<what this milestone marks>",
      "phase": "<phase it belongs to>"
    }
  ],
  "risks": [
    {
      "risk": "<risk description>",
      "mitigation": "<how to mitigate it>"
    }
  ]
}
"""

_SYSTEM_HUMAN_READABLE = """You are a technical writer.
Write a clear, human-readable implementation plan document from the provided structured plan JSON.

The document must include:
1. Executive summary
2. Phase-by-phase breakdown with goals and deliverables
3. Key milestones
4. Risk register

Use plain text with section headers (no markdown). Be concise and precise.
"""


class WorkflowPlanGenerator:
    """Use an LLM to generate the structured ImplementationPlan and human-readable text."""

    def __init__(self, llm=None) -> None:
        self._llm = llm

    def generate(
        self,
        project_config: Dict[str, Any],
        stories: List[Dict[str, Any]],
        features: List[Dict[str, Any]],
        blueprint: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate the ImplementationPlan.

        Args:
            project_config: Structured config from ConfigAnalyzer.
            stories:        Normalised stories.
            features:       Identified features.
            blueprint:      MasterBlueprint from ArchitectureBlueprintGenerator.

        Returns:
            ImplementationPlan dict including a 'text_plan' key.
        """
        import json

        context = (
            f"PROJECT: {project_config.get('project_name')}\n"
            f"TECH STACK: {json.dumps(project_config.get('tech_stack', {}))}\n\n"
            f"FEATURES:\n"
            + "\n".join(f"- {f['name']}: {f.get('description','')[:100]}" for f in features)
            + f"\n\nSTORIES:\n"
            + "\n".join(f"- [{s['id']}] {s['title']} (priority: {s.get('priority','medium')})" for s in stories)
            + f"\n\nMODULES:\n"
            + "\n".join(f"- {m['name']}: {m.get('description','')[:100]}" for m in blueprint.get("modules", []))
        )

        logger.info("WorkflowPlanGenerator: generating structured implementation plan")
        raw = self._llm.complete(_SYSTEM_STRUCTURED, context)
        plan = safe_extract_json(raw, fallback={})

        plan.setdefault("project_name", project_config.get("project_name", "Generated Platform"))
        plan.setdefault("phases", [])
        plan.setdefault("milestones", [])
        plan.setdefault("risks", [])

        logger.info("WorkflowPlanGenerator: generating human-readable implementation plan")
        plan_json_str = json.dumps(plan, indent=2)
        text_plan = self._llm.complete(_SYSTEM_HUMAN_READABLE, plan_json_str)
        plan["text_plan"] = text_plan.strip()

        return plan
