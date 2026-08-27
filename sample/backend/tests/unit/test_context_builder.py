"""Unit tests for ContextBuilder in Knowledge Service."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.base import Base
from app.services.knowledge_service.context_builder import ContextBuilder
from app.services.knowledge_service.exceptions import StoryNotFoundError
from app.models.blueprint import Blueprint
from app.models.component import Component
from app.models.dependency import Dependency
from app.models.epic import Epic
from app.models.file import File
from app.models.generation_history import GenerationHistory
from app.models.project import Project
from app.models.story import Story
from app.schemas.context import GenerationContext


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


def test_build_generation_context_success(db_session):
    """Verify build_generation_context gathers all 9 context fields correctly."""
    # 1. Seed test data
    project = Project(name="Test Platform", description="Test Project", status="active")
    db_session.add(project)
    db_session.commit()

    blueprint = Blueprint(
        project_id=project.id,
        version=1,
        architecture="Microservices Architecture",
        folder_structure={"backend": ["app/main.py"]},
        api_blueprint={"endpoints": ["/api/v1/auth"]},
        workflow_blueprint={"steps": ["login", "verify"]},
        shared_components={"logger": "shared/logger.py", "auth_middleware": "shared/auth.py"},
    )
    db_session.add(blueprint)
    db_session.commit()

    epic = Epic(
        project_id=project.id,
        blueprint_id=blueprint.id,
        epic_key="EPIC-101",
        title="Authentication Epic",
        priority="high",
    )
    db_session.add(epic)
    db_session.commit()

    target_story = Story(
        epic_id=epic.id,
        story_key="US-101",
        title="User Login Endpoint",
        description="As a user I want to log in",
        acceptance_criteria={"rules": ["Must return JWT"]},
        status="approved",
        approved=True,
    )
    sibling_story = Story(
        epic_id=epic.id,
        story_key="US-102",
        title="User Logout Endpoint",
        description="As a user I want to log out",
        status="pending",
    )
    db_session.add_all([target_story, sibling_story])
    db_session.commit()

    comp1 = Component(
        project_id=project.id,
        name="AuthService",
        type="backend_service",
        path="backend/services/auth.py",
        created_by_agent="Agent-1",
    )
    comp2 = Component(
        project_id=project.id,
        name="TokenUtility",
        type="shared_util",
        path="shared/utils/token.py",
        created_by_agent="Agent-1",
    )
    db_session.add_all([comp1, comp2])
    db_session.commit()

    dep = Dependency(
        component_id=comp1.id,
        depends_on_component_id=comp2.id,
        dependency_type="uses",
    )
    db_session.add(dep)
    db_session.commit()

    file1 = File(
        component_id=comp1.id,
        story_id=target_story.id,
        path="backend/services/auth.py",
        version=1,
    )
    db_session.add(file1)
    db_session.commit()

    gen_hist = GenerationHistory(
        story_id=target_story.id,
        agent="Agent-1",
        action="Generate Blueprint",
        status="success",
        execution_time=1.23,
    )
    db_session.add(gen_hist)
    db_session.commit()

    # 2. Execute ContextBuilder
    builder = ContextBuilder(db=db_session)
    context = builder.build_generation_context("US-101")

    # 3. Assert context fields
    assert isinstance(context, GenerationContext)
    assert context.story.story_key == "US-101"
    assert context.story.title == "User Login Endpoint"
    assert context.blueprint is not None
    assert context.blueprint.version == 1
    assert context.blueprint.architecture == "Microservices Architecture"
    assert len(context.existing_components) == 2
    assert "logger" in context.shared_components
    assert len(context.related_stories) == 1
    assert context.related_stories[0].story_key == "US-102"
    assert len(context.files_to_modify) == 1
    assert context.files_to_modify[0].path == "backend/services/auth.py"
    assert len(context.dependencies) == 1
    assert context.dependencies[0].dependency_type == "uses"
    assert len(context.generation_history) == 1
    assert context.generation_history[0].agent == "Agent-1"
    assert context.traceability.story_id == target_story.id


def test_build_generation_context_story_not_found(db_session):
    """Verify StoryNotFoundError is raised when story_id does not exist."""
    builder = ContextBuilder(db=db_session)
    with pytest.raises(StoryNotFoundError) as exc_info:
        builder.build_generation_context("NON-EXISTENT-STORY")
    assert "NON-EXISTENT-STORY" in str(exc_info.value)
