"""Prompt Builder — Assembles prompt templates for Agent-2 LLM Code Generation.

Reuses existing prompt files in backend/prompts/agent2/ and backend/prompts/common/.
"""

import os
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Base prompts directory relative to backend root
_BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROMPTS_DIR = os.path.join(_BACKEND_ROOT, "prompts")


class PromptBuilder:
    """Loads and formats prompt templates for Agent-2 artifact generators."""

    def __init__(self, base_prompts_dir: Optional[str] = None) -> None:
        self.prompts_dir = base_prompts_dir or PROMPTS_DIR

    def load_prompt_template(self, relative_path: str) -> str:
        """Load prompt template text from file system."""
        full_path = os.path.join(self.prompts_dir, relative_path)
        if os.path.exists(full_path):
            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read().strip()
        return ""

    def build_generation_prompt(
        self,
        artifact_type: str,
        story: Dict[str, Any],
        decision: Dict[str, Any],
        blueprint: Optional[Dict[str, Any]] = None,
        tech_stack: str = "Python FastAPI / React",
    ) -> str:
        """Build a formatted LLM prompt for generating code for a specific artifact type.

        Args:
            artifact_type: One of "backend", "frontend", "database", "api", "test".
            story: User story dictionary.
            decision: ComponentDecisionEngine decision dictionary.
            blueprint: Blueprint dictionary.
            tech_stack: Tech stack description.

        Returns:
            Formatted prompt string for LLM completion.
        """
        template_filename = f"generate_{artifact_type}.txt"
        template_path = os.path.join("agent2", template_filename)
        base_template = self.load_prompt_template(template_path)

        story_key = story.get("story_key") or story.get("key") or "US-001"
        story_title = story.get("title", "")
        story_desc = story.get("description", "")
        criteria = story.get("acceptance_criteria", {})

        system_instruction = (
            f"You are a Senior Software Engineer generating production-grade {artifact_type.upper()} code.\n"
            f"Tech Stack: {tech_stack}\n"
            f"Story: [{story_key}] {story_title}\n"
            f"Description: {story_desc}\n"
            f"Acceptance Criteria: {criteria}\n"
            f"Action: {decision.get('action', 'CREATE')}\n"
            f"Module/Component Name: {decision.get('component_name', 'Component')}\n"
        )

        prompt = f"{system_instruction}\n"
        if base_template:
            prompt += f"Guidelines:\n{base_template}\n\n"

        prompt += (
            "Generate complete, executable, clean code only without markdown wrap if possible, "
            "or wrapped in standard markdown blocks."
        )

        return prompt
