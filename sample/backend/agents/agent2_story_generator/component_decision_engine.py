"""Component Decision Engine — Analyzes story context and decides component action.

Evaluates story context, semantic analysis, and blueprint to classify recommended action
(CREATE, MODIFY, REUSE, IGNORE) and determine target generation files.
"""

import logging
from enum import Enum
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class _RecommendedAction(str, Enum):
    """Local mirror of RecommendedAction to avoid circular import through app.schemas."""
    CREATE = "CREATE"
    MODIFY = "MODIFY"
    REUSE = "REUSE"
    IGNORE = "IGNORE"


class ComponentDecisionEngine:
    """Evaluates user story context to decide generation strategy and component targets."""

    def __init__(self, llm: Optional[Any] = None) -> None:
        self.llm = llm

    def decide(
        self,
        story: Dict[str, Any],
        blueprint: Optional[Dict[str, Any]] = None,
        existing_components: Optional[List[Dict[str, Any]]] = None,
        semantic_analysis: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Analyze story context and produce a decision plan.

        Args:
            story: Dict representing the user story (key, title, description, acceptance_criteria).
            blueprint: Dict representing master blueprint / folder structure.
            existing_components: List of components already present in project.
            semantic_analysis: Semantic analysis output from Knowledge Service.

        Returns:
            Dict containing decision details (action, component_name, target_files).
        """
        story_key = story.get("story_key") or story.get("key") or "US-001"
        story_title = story.get("title", "")
        story_desc = story.get("description", "")

        # Default action
        action = _RecommendedAction.CREATE
        if semantic_analysis and isinstance(semantic_analysis, dict):
            rec_action = semantic_analysis.get("recommended_action")
            if rec_action in [e.value for e in _RecommendedAction]:
                action = _RecommendedAction(rec_action)

        # Sanitize story name for component title
        slug_title = "".join(c if c.isalnum() else "_" for c in story_title.lower()).strip("_")
        clean_slug = "_".join(filter(None, slug_title.split("_")))[:30] or "component"

        target_files = {
            "backend": f"backend/{clean_slug}/service.py",
            "frontend": f"frontend/{clean_slug}/Component.jsx",
            "database": f"database/migrations/{clean_slug}_schema.sql",
            "api": f"backend/{clean_slug}/router.py",
            "test": f"backend/tests/test_{clean_slug}.py",
        }

        decision = {
            "story_key": story_key,
            "action": action.value if hasattr(action, "value") else str(action),
            "component_name": clean_slug.title().replace("_", ""),
            "module_name": clean_slug,
            "target_files": target_files,
            "reasoning": f"Decision for story {story_key}: Action={action} based on story title '{story_title}'",
        }

        logger.info("Decision Engine evaluated story %s -> Action: %s", story_key, decision["action"])
        return decision
