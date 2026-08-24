"""Semantic Analyzer service — Read-only requirement classification layer.

Analyzes a user story relative to its GenerationContext to determine whether
the story represents a NEW_FEATURE, MODIFICATION, EXTENSION, or DUPLICATE.

Strict Constraints:
- Read-only: Does NOT modify the database or files.
- Pure analysis: Does NOT generate code.
- Uses GenerationContext and Repositories for project state.
"""

import logging
import re
from typing import Any

from app.services.knowledge_service.exceptions import SemanticAnalyzerError
from app.schemas.context import GenerationContext
from app.schemas.semantic import ChangeType, RecommendedAction, SemanticAnalysisResult

logger = logging.getLogger(__name__)

# Action verbs signaling modification
MODIFICATION_VERBS = {
    "modify",
    "update",
    "change",
    "fix",
    "refactor",
    "patch",
    "correct",
    "revise",
    "delete",
    "remove",
    "bugfix",
}

# Stop words for keyword extraction
STOP_WORDS = {
    "the",
    "and",
    "for",
    "with",
    "user",
    "can",
    "i",
    "want",
    "so",
    "that",
    "to",
    "a",
    "an",
    "as",
    "of",
    "be",
    "is",
    "in",
    "on",
    "at",
    "by",
    "from",
    "it",
    "this",
    "should",
    "must",
    "allow",
    "able",
}


class SemanticAnalyzer:
    """Read-only analyzer that classifies story requirements relative to project context."""

    def analyze_story(
        self, story: Any, generation_context: GenerationContext
    ) -> SemanticAnalysisResult:
        """Classify how a target user story relates to the existing project context.

        :param story: User story object (StoryOut, StoryCreate, Story ORM, or dict).
        :param generation_context: GenerationContext returned by ContextBuilder.
        :return: Strongly typed SemanticAnalysisResult.
        :raises SemanticAnalyzerError: If inputs are invalid or analysis fails.
        """
        logger.info("Starting semantic analysis for story requirements...")

        if not generation_context:
            raise SemanticAnalyzerError("GenerationContext cannot be None.")

        try:
            # 1. Normalize story attributes
            story_title, story_desc, story_id_key = self._extract_story_details(story)
            story_tokens = self._extract_tokens(f"{story_title} {story_desc}")

            logger.debug(
                f"Analyzing story key='{story_id_key}' title='{story_title}' with tokens={story_tokens}"
            )

            # 2. Check for DUPLICATE story
            duplicate_result = self._check_duplicate(
                story_title, story_tokens, generation_context
            )
            if duplicate_result:
                return duplicate_result

            # 3. Check for MODIFICATION
            modification_result = self._check_modification(
                story_tokens, generation_context
            )
            if modification_result:
                return modification_result

            # 4. Check for EXTENSION
            extension_result = self._check_extension(
                story_tokens, generation_context
            )
            if extension_result:
                return extension_result

            # 5. Default to NEW_FEATURE
            return SemanticAnalysisResult(
                change_type=ChangeType.NEW_FEATURE,
                confidence_score=0.90,
                matched_story_ids=[],
                impacted_components=[],
                impacted_files=[],
                reasoning=(
                    f"Story '{story_title}' introduces novel functionality with no matching "
                    "existing components, files, or duplicate requirements in the project."
                ),
                recommended_action=RecommendedAction.CREATE,
            )

        except Exception as exc:
            if isinstance(exc, SemanticAnalyzerError):
                raise
            logger.error(f"Semantic analysis failed: {exc!s}", exc_info=True)
            raise SemanticAnalyzerError(
                f"Semantic analysis failed: {exc!s}"
            ) from exc

    def _extract_story_details(self, story: Any) -> tuple[str, str, str]:
        """Extract title, description, and identifier from story object or dictionary."""
        if isinstance(story, dict):
            title = story.get("title", "")
            desc = story.get("description", "")
            id_key = str(story.get("story_key") or story.get("id") or "UNNAMED")
        else:
            title = getattr(story, "title", "")
            desc = getattr(story, "description", "") or ""
            id_key = str(
                getattr(story, "story_key", None)
                or getattr(story, "id", None)
                or "UNNAMED"
            )

        if not title:
            raise SemanticAnalyzerError("Story must contain a non-empty title.")

        return title, desc, id_key

    def _extract_tokens(self, text: str) -> set[str]:
        """Extract normalized tokens from text excluding stop words."""
        words = re.findall(r"[a-zA-Z0-9]+", text.lower())
        return {w for w in words if w not in STOP_WORDS and len(w) > 1}

    def _check_duplicate(
        self,
        story_title: str,
        story_tokens: set[str],
        context: GenerationContext,
    ) -> SemanticAnalysisResult | None:
        """Identify if the story duplicates an existing story in the context."""
        candidate_stories = context.related_stories[:]
        if context.story and str(context.story.title).lower() != story_title.lower():
            candidate_stories.append(context.story)

        for existing in candidate_stories:
            existing_title = getattr(existing, "title", "")
            existing_desc = getattr(existing, "description", "") or ""
            existing_id = getattr(existing, "id", getattr(existing, "story_key", ""))

            # Exact title match
            if story_title.strip().lower() == existing_title.strip().lower():
                return SemanticAnalysisResult(
                    change_type=ChangeType.DUPLICATE,
                    confidence_score=0.98,
                    matched_story_ids=[existing_id],
                    impacted_components=[],
                    impacted_files=[],
                    reasoning=(
                        f"Story title exact match with existing story '{existing_title}' "
                        f"(ID: {existing_id})."
                    ),
                    recommended_action=RecommendedAction.IGNORE,
                )

            # High token similarity match
            existing_tokens = self._extract_tokens(f"{existing_title} {existing_desc}")
            if story_tokens and existing_tokens:
                intersection = story_tokens.intersection(existing_tokens)
                union = story_tokens.union(existing_tokens)
                similarity = len(intersection) / len(union) if union else 0.0

                if similarity >= 0.75:
                    return SemanticAnalysisResult(
                        change_type=ChangeType.DUPLICATE,
                        confidence_score=round(min(similarity + 0.1, 0.95), 2),
                        matched_story_ids=[existing_id],
                        impacted_components=[],
                        impacted_files=[],
                        reasoning=(
                            f"Requirement text has {similarity:.0%} similarity with "
                            f"existing story '{existing_title}' (ID: {existing_id})."
                        ),
                        recommended_action=RecommendedAction.IGNORE,
                    )

        return None

    def _check_modification(
        self, story_tokens: set[str], context: GenerationContext
    ) -> SemanticAnalysisResult | None:
        """Identify if story requests modification of existing files or components."""
        has_mod_verb = bool(story_tokens.intersection(MODIFICATION_VERBS))

        impacted_files = [f.path for f in context.files_to_modify if f.path]
        impacted_comps = []

        # Find matching components by path or name token overlap
        for comp in context.existing_components:
            comp_name_tokens = self._extract_tokens(f"{comp.name} {comp.path or ''}")
            if story_tokens.intersection(comp_name_tokens):
                impacted_comps.append(comp.name)

        if (has_mod_verb and (impacted_files or impacted_comps)) or (
            impacted_files and has_mod_verb
        ):
            return SemanticAnalysisResult(
                change_type=ChangeType.MODIFICATION,
                confidence_score=0.88,
                matched_story_ids=[context.story.id] if context.story else [],
                impacted_components=impacted_comps,
                impacted_files=impacted_files,
                reasoning=(
                    "Story contains modification keywords and directly targets existing "
                    f"components ({impacted_comps}) or files ({impacted_files})."
                ),
                recommended_action=RecommendedAction.MODIFY,
            )

        return None

    def _check_extension(
        self, story_tokens: set[str], context: GenerationContext
    ) -> SemanticAnalysisResult | None:
        """Identify if story extends an existing component or domain area."""
        matched_comps = []
        matched_files = []

        for comp in context.existing_components:
            comp_tokens = self._extract_tokens(f"{comp.name} {comp.type} {comp.path or ''}")
            overlap = story_tokens.intersection(comp_tokens)
            if overlap:
                matched_comps.append(comp.name)
                if comp.path:
                    matched_files.append(comp.path)

        if matched_comps:
            return SemanticAnalysisResult(
                change_type=ChangeType.EXTENSION,
                confidence_score=0.82,
                matched_story_ids=[context.story.id] if context.story else [],
                impacted_components=matched_comps,
                impacted_files=matched_files,
                reasoning=(
                    f"Story shares domain context with existing component(s) {matched_comps} "
                    "and extends them with additional features."
                ),
                recommended_action=RecommendedAction.REUSE,
            )

        return None
