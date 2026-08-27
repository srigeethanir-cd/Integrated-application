"""Context Builder service — Read-only orchestration layer inside Knowledge Service.

Gathers all necessary project, story, blueprint, component, dependency,
and history context required by downstream AI code generation agents.

Strict Constraints:
- Read-only: Does NOT modify the database.
- Orchestration only: Does NOT generate code or perform semantic reasoning.
- Uses Repositories ONLY for data access (No raw SQL).
"""

import logging
import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from app.services.knowledge_service.exceptions import ContextBuilderError, StoryNotFoundError
from app.repository.blueprint_repository import BlueprintRepository
from app.repository.component_repository import ComponentRepository
from app.repository.dependency_repository import DependencyRepository
from app.repository.epic_repository import EpicRepository
from app.repository.file_repository import FileRepository
from app.repository.generation_history_repository import GenerationHistoryRepository
from app.repository.story_repository import StoryRepository
from app.schemas.ba_accelerator import (
    BlueprintOut,
    ComponentOut,
    FileOut,
    StoryOut,
)
from app.schemas.context import (
    DependencyOut,
    GenerationContext,
    GenerationHistoryOut,
    StoryComponentMapOut,
    TraceabilitySummary,
    ValidationResultOut,
)

logger = logging.getLogger(__name__)


class ContextBuilder:
    """Read-only orchestration layer for building AI code generation context."""

    def __init__(self, db: Session | None = None) -> None:
        """Initialize ContextBuilder with repositories.

        :param db: SQLAlchemy Session. If None, a new session is created.
        """
        self._db_provided = db is not None
        self.db = db or SessionLocal()
        self.story_repo = StoryRepository(self.db)
        self.epic_repo = EpicRepository(self.db)
        self.blueprint_repo = BlueprintRepository(self.db)
        self.component_repo = ComponentRepository(self.db)
        self.file_repo = FileRepository(self.db)
        self.generation_history_repo = GenerationHistoryRepository(self.db)
        self.dependency_repo = DependencyRepository(self.db)

    def close(self) -> None:
        """Close database session if managed internally."""
        if not self._db_provided and self.db:
            self.db.close()

    def build_generation_context(
        self, story_id: uuid.UUID | str
    ) -> GenerationContext:
        """Gather all project, blueprint, component, and history context for a target story.

        :param story_id: Target story primary key (UUID) or story key (str, e.g. "US-001").
        :return: Strongly-typed GenerationContext Pydantic object.
        :raises StoryNotFoundError: If target story cannot be located in the database.
        :raises ContextBuilderError: If an error occurs during context aggregation.
        """
        logger.info(f"Building generation context for story identifier: {story_id}")

        try:
            # 1. Resolve and fetch Target Story
            story_orm = self._resolve_story(story_id)
            if not story_orm:
                raise StoryNotFoundError(str(story_id))

            story_schema = StoryOut.model_validate(story_orm)

            # 2. Retrieve Epic, Blueprint & Project Scope
            epic_orm = self.epic_repo.get(story_orm.epic_id)
            blueprint_schema: BlueprintOut | None = None
            shared_components: dict[str, Any] | list[dict[str, Any]] | None = {}
            related_stories: list[StoryOut] = []
            existing_components: list[ComponentOut] = []

            if epic_orm:
                # Blueprint resolution (by epic's blueprint_id or latest project version)
                blueprint_orm = self.blueprint_repo.get(epic_orm.blueprint_id)
                if not blueprint_orm:
                    blueprint_orm = self.blueprint_repo.get_latest_version(epic_orm.project_id)

                if blueprint_orm:
                    blueprint_schema = BlueprintOut.model_validate(blueprint_orm)
                    shared_components = blueprint_orm.shared_components or {}

                # Related stories in same epic
                epic_stories = self.story_repo.get_by_epic(epic_orm.id)
                related_stories = [
                    StoryOut.model_validate(s)
                    for s in epic_stories
                    if s.id != story_orm.id
                ]

                # Existing components for the project
                project_comps = self.component_repo.get_by_project(epic_orm.project_id)
                existing_components = [
                    ComponentOut.model_validate(c) for c in project_comps
                ]

            # 3. Retrieve Files to Modify / Associated Files
            story_files = self.file_repo.get_by_story(story_orm.id)
            files_to_modify = [FileOut.model_validate(f) for f in story_files]

            # 4. Retrieve Component Dependencies
            comp_ids = [c.id for c in existing_components]
            dep_orms = self.dependency_repo.get_by_components(comp_ids)
            dependencies = [DependencyOut.model_validate(d) for d in dep_orms]

            # 5. Retrieve Generation History
            history_orms = self.generation_history_repo.get_by_story(story_orm.id)
            generation_history = [
                GenerationHistoryOut.model_validate(h) for h in history_orms
            ]

            # 6. Build Traceability Summary
            mapped_components = [
                StoryComponentMapOut.model_validate(scm)
                for scm in (getattr(story_orm, "story_component_maps", []) or [])
            ]
            validations = [
                ValidationResultOut.model_validate(vr)
                for vr in (getattr(story_orm, "validation_results", []) or [])
            ]

            traceability = TraceabilitySummary(
                story_id=story_orm.id,
                mapped_components=mapped_components,
                validations=validations,
                file_changes=files_to_modify,
            )

            # 7. Construct & Return GenerationContext
            context = GenerationContext(
                story=story_schema,
                blueprint=blueprint_schema,
                existing_components=existing_components,
                shared_components=shared_components,
                traceability=traceability,
                dependencies=dependencies,
                generation_history=generation_history,
                files_to_modify=files_to_modify,
                related_stories=related_stories,
            )

            logger.info(
                f"Successfully built generation context for story key: '{story_orm.story_key}'"
            )
            return context

        except StoryNotFoundError:
            raise
        except Exception as exc:
            logger.error(
                f"Failed to build generation context for '{story_id}': {exc!s}",
                exc_info=True,
            )
            raise ContextBuilderError(
                f"Error building generation context for '{story_id}': {exc!s}"
            ) from exc

    def _resolve_story(self, story_id: uuid.UUID | str) -> Any | None:
        """Look up a story ORM instance by UUID primary key or story_key.

        :param story_id: UUID or string key.
        :return: Story ORM object or None.
        """
        if isinstance(story_id, uuid.UUID):
            return self.story_repo.get_by_id(story_id)

        # Attempt parsing string as UUID
        try:
            parsed_uuid = uuid.UUID(story_id)
            story = self.story_repo.get_by_id(parsed_uuid)
            if story:
                return story
        except ValueError:
            pass

        # Fallback to story_key lookup
        # pyrefly: ignore [unnecessary-type-conversion]
        return self.story_repo.get_by_key(str(story_id))
