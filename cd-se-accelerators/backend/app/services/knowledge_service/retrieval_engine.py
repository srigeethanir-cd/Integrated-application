"""Retrieval Engine service — Single interface between Agent-2 and Knowledge Service.

Orchestrates the retrieval of complete project context by coordinating between
the ContextBuilder and SemanticAnalyzer services.

Strict Constraints:
- Read-only: Does NOT modify database, files, or generate code.
- Facade: Orchestrates existing Knowledge Service components.
- No raw SQL.
"""

import logging
import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.services.knowledge_service.context_builder import ContextBuilder
from app.services.knowledge_service.exceptions import (
    KnowledgeServiceError,
    RetrievalEngineError,
    StoryNotFoundError,
)
from app.services.knowledge_service.semantic_analyzer import SemanticAnalyzer
from app.schemas.context import GenerationContext

logger = logging.getLogger(__name__)


class RetrievalEngine:
    """Single interface between Agent-2 and Knowledge Service for generation context retrieval."""

    def __init__(
        self,
        db: Session | None = None,
        context_builder: ContextBuilder | None = None,
        semantic_analyzer: SemanticAnalyzer | None = None,
    ) -> None:
        """Initialize RetrievalEngine with dependent services.

        :param db: Optional SQLAlchemy Session.
        :param context_builder: Optional custom ContextBuilder instance.
        :param semantic_analyzer: Optional custom SemanticAnalyzer instance.
        """
        self.db = db
        self.context_builder = context_builder or ContextBuilder(db=db)
        self.semantic_analyzer = semantic_analyzer or SemanticAnalyzer()

    def retrieve_generation_context(
        self, story_id: uuid.UUID | str
    ) -> GenerationContext:
        """Retrieve complete project, blueprint, component, traceability, and semantic analysis context for Agent-2.

        :param story_id: Target user story UUID or story key string (e.g. "US-101").
        :return: Fully populated GenerationContext Pydantic object for Agent-2.
        :raises StoryNotFoundError: If the requested story cannot be found.
        :raises RetrievalEngineError: If an error occurs during retrieval or semantic analysis.
        """
        logger.info(f"Retrieving generation context for story_id='{story_id}'")

        try:
            # 1. Build initial context via ContextBuilder
            context: GenerationContext = self.context_builder.build_generation_context(
                story_id
            )

            # 2. Perform semantic analysis via SemanticAnalyzer
            semantic_result = self.semantic_analyzer.analyze_story(
                context.story, context
            )

            # 3. Enrich context with semantic analysis and recommended action
            context.semantic_analysis = semantic_result
            context.recommended_action = semantic_result.recommended_action

            logger.info(
                f"Successfully retrieved generation context for story '{context.story.story_key}' "
                f"with change_type='{semantic_result.change_type.value}' and action='{semantic_result.recommended_action.value}'"
            )
            return context

        except StoryNotFoundError:
            raise
        except KnowledgeServiceError as exc:
            logger.error(f"Knowledge service error during context retrieval for '{story_id}': {exc!s}")
            raise RetrievalEngineError(
                f"Failed to retrieve generation context for '{story_id}': {exc!s}"
            ) from exc
        except Exception as exc:
            logger.error(f"Unexpected error during context retrieval for '{story_id}': {exc!s}", exc_info=True)
            raise RetrievalEngineError(
                f"Unexpected error retrieving context for '{story_id}': {exc!s}"
            ) from exc
