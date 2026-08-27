"""Unit tests for RetrievalEngine in Knowledge Service."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.base import Base
from app.services.knowledge_service.exceptions import StoryNotFoundError
from app.services.knowledge_service.retrieval_engine import RetrievalEngine
from app.models.blueprint import Blueprint
from app.models.component import Component
from app.models.dependency import Dependency
from app.models.epic import Epic
from app.models.file import File
from app.models.generation_history import GenerationHistory
from app.models.project import Project
from app.models.story import Story
from app.schemas.context import GenerationContext
from app.schemas.semantic import RecommendedAction


@pytest.fixture
def db_session():
    """Create an in-memory SQLite database session for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    session = Session()
    try:
        yield session
    finally:
        session.close()


def test_retrieve_generation_context_success(db_session):
    """Verify RetrievalEngine retrieves context and populates semantic_analysis and recommended_action."""
    # 1. Seed database
    project = Project(name="Agent-2 Platform", description="Test Project", status="active")
    db_session.add(project)
    db_session.commit()

    blueprint = Blueprint(
        project_id=project.id,
        version=1,
        architecture="Clean Architecture",
        folder_structure={"backend": ["app/main.py"]},
        api_blueprint={"endpoints": ["POST /api/v1/auth/login"]},
        shared_components={"logger": "shared/logger.py"},
    )
    db_session.add(blueprint)
    db_session.commit()

    epic = Epic(
        project_id=project.id,
        blueprint_id=blueprint.id,
        epic_key="EPIC-201",
        title="Authentication System",
    )
    db_session.add(epic)
    db_session.commit()

    story = Story(
        epic_id=epic.id,
        story_key="US-201",
        title="User Login Service",
        description="Implement JWT authentication login endpoint",
        status="approved",
        approved=True,
    )
    sibling = Story(
        epic_id=epic.id,
        story_key="US-202",
        title="User Registration",
        description="Implement user registration",
    )
    db_session.add_all([story, sibling])
    db_session.commit()

    comp = Component(
        project_id=project.id,
        name="AuthService",
        type="service",
        path="backend/services/auth.py",
        created_by_agent="Agent-1",
    )
    db_session.add(comp)
    db_session.commit()

    file_obj = File(
        component_id=comp.id,
        story_id=story.id,
        path="backend/services/auth.py",
        version=1,
    )
    db_session.add(file_obj)
    db_session.commit()

    gen_hist = GenerationHistory(
        story_id=story.id,
        agent="Agent-1",
        action="Generate Blueprint",
        status="success",
    )
    db_session.add(gen_hist)
    db_session.commit()

    # 2. Invoke RetrievalEngine
    engine_instance = RetrievalEngine(db=db_session)
    context = engine_instance.retrieve_generation_context("US-201")

    # 3. Assert full GenerationContext container for Agent-2
    assert isinstance(context, GenerationContext)
    assert context.story.story_key == "US-201"
    assert context.blueprint is not None
    assert context.blueprint.version == 1
    assert len(context.existing_components) == 1
    assert "logger" in context.shared_components
    assert len(context.related_stories) == 1
    assert len(context.generation_history) == 1
    assert len(context.files_to_modify) == 1

    # Assert semantic analysis integration
    assert context.semantic_analysis is not None
    assert context.recommended_action is not None
    assert context.recommended_action in (
        RecommendedAction.CREATE,
        RecommendedAction.MODIFY,
        RecommendedAction.REUSE,
        RecommendedAction.IGNORE,
    )


def test_retrieve_generation_context_story_not_found(db_session):
    """Verify StoryNotFoundError is raised when story is missing."""
    engine_instance = RetrievalEngine(db=db_session)
    with pytest.raises(StoryNotFoundError):
        engine_instance.retrieve_generation_context("INVALID-STORY-ID")
