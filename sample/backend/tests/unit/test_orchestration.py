import os
import json
import pytest
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.project import Base
from app.models import (
    DependencyGraphRecord,
    ExecutionTimelineRecord,
    SharedArtifactRegistryRecord,
    RollbackHistoryRecord,
    AgentExecutionMetric
)
from story_orchestration.dependency_resolver import StoryDependencyResolver
from story_orchestration.execution_scheduler import StoryExecutionScheduler
from story_shared.artifact_registry import SharedArtifactRegistry
from story_database.migration_planner import DatabaseMigrationPlanner
from validators.cross_story_validator import CrossStoryValidator
from merger.merge_queue import DependencyAwareMergeQueue
from story_orchestration.project_orchestrator import ProjectOrchestrator

@pytest.fixture
def db_session():
    """Create an in-memory SQLite database session for testing."""
    engine = create_engine("sqlite:///:memory:", echo=True)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


def test_story_dependency_resolver(db_session):
    """Verify resolver orders execution sequence and commits graph to DB."""
    resolver = StoryDependencyResolver(db=db_session, project_id="PROJ-001")
    stories = [
        {"story_key": "US102", "title": "User login system", "description": "Needs to authenticate"},
        {"story_key": "US101", "title": "Create User accounts", "description": "Registers new users"}
    ]
    res = resolver.resolve_dependencies(stories)
    
    assert res["execution_order"] == ["US101", "US102"]
    
    # Assert database record was committed
    graph_rec = db_session.query(DependencyGraphRecord).filter_by(project_id="PROJ-001").first()
    assert graph_rec is not None
    assert graph_rec.execution_order_json == ["US101", "US102"]


def test_story_execution_scheduler(db_session):
    """Verify scheduler executes independent stories in parallel and tracks DB metrics."""
    scheduler = StoryExecutionScheduler(db=db_session, project_id="PROJ-001", max_workers=2)
    stories = [
        {"story_key": "US101", "title": "Create User"},
        {"story_key": "US102", "title": "Login"}
    ]
    execution_order = ["US101", "US102"]
    dependency_graph = {"US102": ["US101"]}

    completed_runs = []
    def mock_run(story):
        completed_runs.append(story["story_key"])
        return {"success": True}

    res = scheduler.execute_queue(stories, execution_order, dependency_graph, mock_run)
    assert res["status"] == "COMPLETED"
    assert completed_runs == ["US101", "US102"]

    # Assert scheduler state persisted in DB
    timeline_rec = db_session.query(ExecutionTimelineRecord).filter_by(project_id="PROJ-001").first()
    assert timeline_rec is not None
    assert timeline_rec.scheduler_state_json["queue"]["US102"] == "completed"

    # Assert Agent Execution Metrics logged in DB
    metrics = db_session.query(AgentExecutionMetric).filter_by(project_id="PROJ-001").all()
    assert len(metrics) == 2
    assert metrics[0].execution_state == "SUCCESS"


def test_shared_artifact_registry(db_session):
    """Verify registry logs and finds reusable modules in DB."""
    registry = SharedArtifactRegistry(db=db_session, project_id="PROJ-001")
    
    # Register AuthService
    registry.register_artifact("shared_services", "AuthService", "shared/services/auth.py", "US101")
    
    found = registry.find_reusable_artifact("shared_services", "AuthService")
    assert found is not None
    assert found["owner_story"] == "US101"

    # Assert record exists in database table
    db_rec = db_session.query(SharedArtifactRegistryRecord).filter_by(project_id="PROJ-001", name="AuthService").first()
    assert db_rec is not None
    assert db_rec.file_path == "shared/services/auth.py"


def test_database_migration_planner(db_session):
    """Verify migration planner orders DDL schemas."""
    planner = DatabaseMigrationPlanner(db=db_session, project_id="PROJ-001")
    migrations = [
        {"story_key": "US102", "table_name": "profiles", "foreign_keys": ["users"]},
        {"story_key": "US101", "table_name": "users", "foreign_keys": []}
    ]
    res = planner.plan_migrations(migrations)
    
    assert res["execution_order"] == ["users", "profiles"]


def test_cross_story_validator(tmp_path):
    """Verify validator flags collision in api path endpoints."""
    # Write colliding mock endpoint files in epics
    (tmp_path / "epics" / "EP001" / "US101" / "backend").mkdir(parents=True)
    (tmp_path / "epics" / "EP001" / "US102" / "backend").mkdir(parents=True)
    
    (tmp_path / "epics" / "EP001" / "US101" / "backend" / "service.py").write_text("@router.get('/api/users')\ndef run(): pass")
    (tmp_path / "epics" / "EP001" / "US102" / "backend" / "service.py").write_text("@router.get('/api/users')\ndef run2(): pass")

    validator = CrossStoryValidator(workspace_root=tmp_path)
    approved = [
        {"story_key": "US101", "epic_key": "EP001"},
        {"story_key": "US102", "epic_key": "EP001"}
    ]
    res = validator.validate_cross_stories(approved)
    
    assert res["passed"] is False
    assert len(res["errors"]) == 1
    assert "US101" in res["failed_stories"]


def test_dependency_aware_merge_queue(db_session, tmp_path):
    """Verify merge queue manages incremental commits and rollbacks in DB."""
    integrated_dir = tmp_path / "integrated_project"
    integrated_dir.mkdir()
    (integrated_dir / "app.py").write_text("initial state")

    queue = DependencyAwareMergeQueue(
        db=db_session,
        project_id="PROJ-001",
        workspace_root=tmp_path,
        integrated_project_root=integrated_dir
    )

    approved = [
        {"story_key": "US101"},
        {"story_key": "US102"}
    ]
    execution_order = ["US101", "US102"]
    dependency_graph = {"US102": ["US101"]}

    # Simulate success on US101 but conflict on US102
    def mock_merge(s_key):
        if s_key == "US101":
            (integrated_dir / "app.py").write_text("US101 integrated")
            return {"success": True}
        else:
            return {"success": False, "error": "conflict"}

    res = queue.execute_merges(approved, execution_order, dependency_graph, mock_merge)
    
    assert "US101" in res["merged"]
    assert "US102" in res["conflicts"]
    
    # Assert database has rollback log committed
    rollback_rec = db_session.query(RollbackHistoryRecord).filter_by(project_id="PROJ-001", story_key="US102").first()
    assert rollback_rec is not None
    assert rollback_rec.reason == "conflict"
