"""Unit tests for SemanticAnalyzer in Knowledge Service."""

import uuid
import pytest

from app.services.knowledge_service.exceptions import SemanticAnalyzerError
from app.services.knowledge_service.semantic_analyzer import SemanticAnalyzer
from app.schemas.ba_accelerator import BlueprintOut, ComponentOut, FileOut, StoryOut
from app.schemas.context import GenerationContext
from app.schemas.semantic import ChangeType, RecommendedAction, SemanticAnalysisResult


@pytest.fixture
def sample_context():
    """Create sample GenerationContext for semantic analysis testing."""
    story_id = uuid.uuid4()
    epic_id = uuid.uuid4()

    story = StoryOut(
        id=story_id,
        epic_id=epic_id,
        story_key="US-101",
        title="User Login Endpoint",
        description="User can login with email and password",
        acceptance_criteria={"rules": ["Must return JWT"]},
        status="approved",
        approved=True,
        created_at="2026-07-20T10:00:00Z",
    )

    component = ComponentOut(
        id=uuid.uuid4(),
        project_id=uuid.uuid4(),
        name="AuthService",
        type="service",
        path="backend/services/auth.py",
        description="Authentication Service",
        created_by_agent="Agent-1",
        created_at="2026-07-20T10:00:00Z",
    )

    file_obj = FileOut(
        id=uuid.uuid4(),
        component_id=component.id,
        story_id=story_id,
        path="backend/services/auth.py",
        hash="hash123",
        version=1,
        created_at="2026-07-20T10:00:00Z",
    )

    related_story = StoryOut(
        id=uuid.uuid4(),
        epic_id=epic_id,
        story_key="US-102",
        title="User Logout Endpoint",
        description="User can logout of current session",
        acceptance_criteria=None,
        status="pending",
        approved=False,
        created_at="2026-07-20T10:00:00Z",
    )

    return GenerationContext(
        story=story,
        blueprint=None,
        existing_components=[component],
        shared_components={},
        traceability={"story_id": story_id, "mapped_components": [], "validations": [], "file_changes": [file_obj]},
        dependencies=[],
        generation_history=[],
        files_to_modify=[file_obj],
        related_stories=[related_story],
    )


def test_analyze_story_duplicate(sample_context):
    """Verify duplicate story title is classified as DUPLICATE and IGNORE."""
    analyzer = SemanticAnalyzer()
    duplicate_story = {"title": "User Logout Endpoint", "description": "User can logout"}

    result = analyzer.analyze_story(duplicate_story, sample_context)

    assert isinstance(result, SemanticAnalysisResult)
    assert result.change_type == ChangeType.DUPLICATE
    assert result.recommended_action == RecommendedAction.IGNORE
    assert result.confidence_score >= 0.90
    assert len(result.matched_story_ids) == 1


def test_analyze_story_modification(sample_context):
    """Verify story requesting refactoring/fix is classified as MODIFICATION and MODIFY."""
    analyzer = SemanticAnalyzer()
    mod_story = {
        "title": "Fix and update AuthService password check",
        "description": "Modify backend/services/auth.py to fix password validation bug",
    }

    result = analyzer.analyze_story(mod_story, sample_context)

    assert result.change_type == ChangeType.MODIFICATION
    assert result.recommended_action == RecommendedAction.MODIFY
    assert "AuthService" in result.impacted_components
    assert "backend/services/auth.py" in result.impacted_files


def test_analyze_story_extension(sample_context):
    """Verify story extending domain component is classified as EXTENSION and REUSE."""
    analyzer = SemanticAnalyzer()
    ext_story = {
        "title": "Add MFA to AuthService",
        "description": "Extend AuthService to support multi-factor authentication",
    }

    result = analyzer.analyze_story(ext_story, sample_context)

    assert result.change_type == ChangeType.EXTENSION
    assert result.recommended_action == RecommendedAction.REUSE
    assert "AuthService" in result.impacted_components


def test_analyze_story_new_feature(sample_context):
    """Verify story for unrelated domain is classified as NEW_FEATURE and CREATE."""
    analyzer = SemanticAnalyzer()
    new_story = {
        "title": "Process Order Payment",
        "description": "User can checkout and pay via Stripe credit card",
    }

    result = analyzer.analyze_story(new_story, sample_context)

    assert result.change_type == ChangeType.NEW_FEATURE
    assert result.recommended_action == RecommendedAction.CREATE
    assert result.confidence_score >= 0.85
    assert result.impacted_components == []


def test_analyze_story_invalid_input(sample_context):
    """Verify SemanticAnalyzerError is raised for invalid inputs."""
    analyzer = SemanticAnalyzer()
    with pytest.raises(SemanticAnalyzerError):
        analyzer.analyze_story(None, sample_context)

    with pytest.raises(SemanticAnalyzerError):
        analyzer.analyze_story({"title": ""}, sample_context)
