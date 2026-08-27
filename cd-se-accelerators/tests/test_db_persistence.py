"""
Test Database Persistence, Repository CRUD operations, and Project API Endpoints.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base
from app.db.repository import ProjectRepository
from app.db.models import (
    Project,
    PipelineRun,
    Component,
    TestCaseModel,
    TestFileModel,
    TestExecutionModel,
    ReportModel,
)


@pytest.fixture
def db_session():
    """Create in-memory SQLite database session for testing repository logic."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_project_and_pipeline_run_crud(db_session):
    repo = ProjectRepository(db_session)
    
    # 1. Create project
    proj = repo.create_project(
        project_id="proj_test_001",
        project_name="Test Project",
        project_path="/tmp/test_proj",
        framework="React",
    )
    assert proj.id == "proj_test_001"
    assert proj.project_name == "Test Project"
    assert proj.framework == "React"

    # 2. Create pipeline run
    run = repo.create_pipeline_run(
        pipeline_run_id="run_test_001",
        project_id="proj_test_001",
        current_stage="source_ingestion",
        status="running",
    )
    assert run.id == "run_test_001"
    assert run.project_id == "proj_test_001"

    # 3. Update pipeline run stage
    updated_run = repo.update_pipeline_run_stage(
        pipeline_run_id="run_test_001",
        current_stage="validation",
        progress=1.0,
        status="completed",
    )
    assert updated_run.current_stage == "validation"
    assert updated_run.status == "completed"
    assert updated_run.progress == 1.0


def test_components_and_test_cases_persistence(db_session):
    repo = ProjectRepository(db_session)
    repo.create_project("proj_002", "Sample Proj", "/tmp/sample")
    repo.create_pipeline_run("run_002", "proj_002")

    # Save components
    comps = [
        {"name": "LoginForm", "component_type": "ReactComponent"},
        {"name": "EmailInput", "component_type": "ReactComponent"},
    ]
    saved_comps = repo.save_components("proj_002", "run_002", comps, framework="React")
    assert len(saved_comps) == 2
    assert saved_comps[0].name == "LoginForm"

    # Save test cases
    tc_list = [
        {
            "id": "TC-LOGIN-001",
            "component": "LoginForm",
            "title": "Verify login with valid credentials",
            "objective": "Ensure form submits cleanly",
            "category": "Form Validation",
            "priority": "High",
            "steps": ["Enter email", "Enter password", "Click Submit"],
            "expected_result": "Form submits",
        },
        {
            "id": "TC-EMAIL-001",
            "component": "EmailInput",
            "title": "Verify email input validation",
            "objective": "Reject invalid email",
            "category": "Validation",
            "priority": "Medium",
            "steps": ["Enter bad email"],
            "expected_result": "Error shown",
        },
    ]
    saved_cases = repo.save_test_cases("proj_002", "run_002", tc_list)
    assert len(saved_cases) == 2

    # Query test cases
    retrieved = repo.get_test_cases_by_project("proj_002")
    assert len(retrieved) == 2
    assert retrieved[0].id == "proj_002_TC-LOGIN-001"
    assert retrieved[1].id == "proj_002_TC-EMAIL-001"



def test_test_files_and_reports_persistence(db_session):
    repo = ProjectRepository(db_session)
    repo.create_project("proj_003", "Report Proj", "/tmp/rep")
    repo.create_pipeline_run("run_003", "proj_003")

    # Save test files
    tf_list = [
        {"file_name": "LoginForm.test.jsx", "file_path": "tests/react/LoginForm.test.jsx", "component": "LoginForm"}
    ]
    saved_files = repo.save_test_files("proj_003", "run_003", tf_list)
    assert len(saved_files) == 1
    assert saved_files[0].file_name == "LoginForm.test.jsx"

    # Save final report
    rep_data = {
        "execution_summary": {"total_tests": 10, "passed": 10, "failed": 0, "skipped": 0, "pass_rate": 100.0},
        "quality_score": {"overall_score": 98.5},
    }
    saved_rep = repo.save_report("proj_003", "run_003", rep_data)
    assert saved_rep is not None
    assert saved_rep.total_tests == 10
    assert saved_rep.pass_rate == 100.0

    # Fetch latest report
    latest = repo.get_latest_report(project_id="proj_003")
    assert latest is not None
    assert latest.overall_quality_score == 98.5
