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
        """Build a detailed, highly accurate LLM prompt for generating production code."""
        template_filename = f"generate_{artifact_type}.txt"
        template_path = os.path.join("agent2", template_filename)
        base_template = self.load_prompt_template(template_path)

        story_key = story.get("story_key") or story.get("key") or decision.get("story_key", "US001")
        story_title = story.get("title") or decision.get("story_title", "")
        story_desc = story.get("description") or decision.get("description", "")
        criteria = story.get("acceptance_criteria") or decision.get("acceptance_criteria", {})
        fields = decision.get("fields", [])
        
        fields_str = ", ".join(f"{f.get('name')} ({f.get('type')})" for f in fields) if fields else "Infer relevant domain fields"

        system_instruction = (
            f"You are an Elite Principal Software Engineer creating production-ready {artifact_type.upper()} code.\n"
            f"Tech Stack: {tech_stack}\n"
            f"User Story: [{story_key}] {story_title}\n"
            f"Description: {story_desc}\n"
            f"Acceptance Criteria:\n{criteria}\n"
            f"Extracted Form & Data Fields: {fields_str}\n"
            f"Target Module: {decision.get('module_name')}\n"
            f"Target Component/Class: {decision.get('component_name') or decision.get('service_name')}\n"
            f"Database Table: {decision.get('table_name')}\n"
            f"Primary Action: {decision.get('primary_action')}\n\n"
            f"CRITICAL REQUIREMENTS FOR {artifact_type.upper()}:\n"
            f"1. Directly implement every acceptance criteria requirement.\n"
            f"2. Use modern, robust idiomatic syntax ({tech_stack}).\n"
            f"3. Include proper validation, error handling, status codes, and type hints.\n"
            f"4. Do NOT use generic placeholder words (e.g. 'foo', 'bar', 'item1'). Use real domain models.\n"
            f"5. Return ONLY executable code directly or enclosed in standard markdown code fence.\n"
        )

        prompt = f"{system_instruction}\n"
        if base_template and len(base_template) > 50:
            prompt += f"Guidelines:\n{base_template}\n\n"

        return prompt
