import os
import json
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.project import Base
from app.models.prompt_template import (
    PromptTemplate,
    PromptTemplateVersion,
    PromptExecutionLog,
    PromptApproval,
    PromptPerformance
)
from app.services.prompt_template_service import PromptTemplateService
from agents.common.prompt_loader import PromptLoader
from agents.common.llm_factory import LLMClientAdapter

@pytest.fixture
def db_session():
    """In-memory SQLite database setup."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


def test_prompt_template_creation_and_versioning(db_session):
    """Verify prompt creation generates initial 1.0 version snapshot."""
    service = PromptTemplateService(db_session)
    t = service.create_template({
        "prompt_code": "agent2_backend_service",
        "prompt_name": "Agent 2 Backend",
        "agent_name": "agent2",
        "prompt_template": "System: {{ system_prompt }}\nUser: {{ user_prompt }}",
        "status": "Approved",
        "is_active": True
    })

    assert t.prompt_version == "1.0"
    
    # Assert version table has the entry
    versions = service.list_versions(t.id)
    assert len(versions) == 1
    assert versions[0].prompt_snapshot == "System: {{ system_prompt }}\nUser: {{ user_prompt }}"


def test_prompt_template_update_and_history(db_session):
    """Verify modifying template increments version and preserves history."""
    service = PromptTemplateService(db_session)
    t = service.create_template({
        "prompt_code": "agent2_backend_service",
        "prompt_name": "Agent 2 Backend",
        "agent_name": "agent2",
        "prompt_template": "System: v1",
        "status": "Approved",
        "is_active": True
    })

    # Update template
    updated = service.update_template(
        template_id=t.id,
        updates={"prompt_template": "System: v2"},
        changed_by="tester",
        change_summary="Upgraded template structure"
    )

    assert updated.prompt_version == "1.1"
    
    versions = service.list_versions(t.id)
    assert len(versions) == 2
    assert versions[0].prompt_snapshot == "System: v1"
    assert versions[1].prompt_snapshot == "System: v2"


def test_prompt_template_rollback(db_session):
    """Verify rollback operation updates active prompt template and records change."""
    service = PromptTemplateService(db_session)
    t = service.create_template({
        "prompt_code": "agent2_backend_service",
        "prompt_name": "Agent 2 Backend",
        "agent_name": "agent2",
        "prompt_template": "System: v1",
        "status": "Approved",
        "is_active": True
    })

    # Update to v2
    service.update_template(t.id, {"prompt_template": "System: v2"}, "tester", "changed v2")

    # Roll back to version number 1 (which holds 'System: v1')
    res = service.rollback_prompt(t.id, 1, "rollback_user")
    assert res["success"] is True
    assert res["new_version"] == "1.2"

    # Active template content should be restored to v1
    active = service.get_template(t.id)
    assert active.prompt_template == "System: v1"


def test_prompt_template_approval(db_session):
    """Verify approval state transitions."""
    service = PromptTemplateService(db_session)
    t = service.create_template({
        "prompt_code": "agent2_backend_service",
        "prompt_name": "Agent 2 Backend",
        "agent_name": "agent2",
        "prompt_template": "System: v1",
        "status": "Pending Review",
        "is_active": False
    })

    res = service.approve_prompt(t.id, "reviewer_bob", "Approved", "Looks good", "1.0")
    assert res["success"] is True
    assert res["status"] == "Approved"

    active = service.get_template(t.id)
    assert active.status == "Approved"
    assert active.is_active is True
