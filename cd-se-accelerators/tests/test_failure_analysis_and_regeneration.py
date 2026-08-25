"""
Automated Verification Suite for Traceability-Based Test Failure Analysis & Targeted Regeneration.
"""

import pytest
from pathlib import Path
from app.db.database import init_db
from app.db.repository import ProjectRepository
from app.services.failure_analysis_service import FailureAnalysisService
from app.services.test_regeneration_service import TestRegenerationService

init_db()



def test_failure_analysis_service_selector_mismatch():
    """Verify FailureAnalysisService classifies selector mismatches correctly."""
    service = FailureAnalysisService()
    
    traceability = {
        "component": {"name": "LoginForm"},
        "function_behavior": "handlePasswordChange()",
        "source_file": "src/components/LoginForm.jsx",
    }
    
    report = service.analyze_failure(
        test_case_id="TC-LOGIN-PWD-001",
        error_message="TestingLibraryElementError: Unable to find an element with the role 'textbox' and name 'Password'",
        stack_trace="Error: Unable to find element\n at Object.getByRole (LoginForm.test.jsx:15)",
        expected="Password input element in document",
        actual="Unable to find element with role 'textbox'",
        traceability=traceability,
    )
    
    assert report.test_case_id == "TC-LOGIN-PWD-001"
    assert report.component == "LoginForm"
    assert report.function == "handlePasswordChange()"
    assert report.mismatch_type == "SelectorMismatch"
    assert report.regeneration_recommended is True


def test_failure_analysis_service_expected_value_mismatch():
    """Verify FailureAnalysisService classifies expected value mismatches."""
    service = FailureAnalysisService()
    
    report = service.analyze_failure(
        test_case_id="TC-AUTH-002",
        error_message="expect(received).toBe(expected)\nExpected: 'Invalid Email'\nReceived: ''",
        expected="Invalid Email",
        actual="",
    )
    
    assert report.mismatch_type == "ExpectedValueMismatch"
    assert "Value assertion mismatch" in report.failure_reason or "Expected" in report.failure_reason


def test_test_regeneration_service_targeted_workflow(tmp_path: Path):
    """Verify targeted single test file regeneration and version incrementing."""
    repo = ProjectRepository()
    proj_id = "proj_test_regen"
    run_id = "run_test_regen"
    tc_id = "TC-FORM-REG-001"

    repo.create_project(proj_id, "Regeneration App", str(tmp_path), "React")
    repo.create_pipeline_run(run_id, proj_id, "validation", "completed")

    tc_data = [{
        "id": tc_id,
        "title": "Email Validation Test",
        "category": "Forms",
        "priority": "High",
        "component": "EmailField",
        "target_function": "validateEmail()",
        "expected_result": "Error message displayed",
        "source_file": "src/components/EmailField.jsx",
        "strategy_id": "STRAT-EMAIL-001",
        "edge_case_id": "EDGE-INVALID-EMAIL",
    }]

    repo.save_test_cases(proj_id, run_id, tc_data)

    # 1. Save Initial Failed Version 1
    repo.save_test_case_version(
        test_case_id=tc_id,
        project_id=proj_id,
        pipeline_run_id=run_id,
        version=1,
        test_file_path=str(tmp_path / "EmailField.test.jsx"),
        test_code="// Version 1 failed test code",
        status="failed",
        regeneration_reason="Initial selector mismatch",
    )

    # 2. Trigger Targeted Regeneration
    regen_service = TestRegenerationService(repo=repo)
    res = regen_service.regenerate_test_case(
        test_case_id=tc_id,
        regeneration_instruction="Correct query selector to use queryByRole",
    )

    assert res.test_case_id == tc_id
    assert res.previous_version == 1
    assert res.new_version == 2
    assert res.new_status == "passed"
    assert "Regenerated Test Suite (Version 2)" in res.updated_test_code

    # 3. Verify Version History Persistence
    versions = repo.get_test_case_versions(tc_id)
    assert len(versions) >= 1
    assert any(v.version == 2 for v in versions)


def test_end_to_end_traceability_retrieval(tmp_path: Path):
    """Verify complete end-to-end traceability hierarchy tree format."""
    repo = ProjectRepository()
    proj_id = "proj_trace_demo"
    run_id = "run_trace_demo"
    tc_id = "TC-TRACE-001"

    repo.create_project(proj_id, "Traceability App", str(tmp_path), "Angular")
    repo.create_pipeline_run(run_id, proj_id, "validation", "completed")

    tc_data = [{
        "id": tc_id,
        "title": "Customer Portal Order Submit",
        "category": "Services",
        "priority": "High",
        "component": "OrderComponent",
        "target_function": "submitOrder()",
        "expected_result": "Order submitted successfully",
        "source_file": "src/app/order.component.ts",
        "strategy_id": "STRAT-ORDER-001",
        "edge_case_id": "EDGE-NETWORK-TIMEOUT",
        "test_data": {"order_id": 4021},
    }]

    repo.save_test_cases(proj_id, run_id, tc_data)

    trace = repo.get_test_case_traceability(tc_id)
    assert trace is not None
    assert trace["project"]["project_name"] == "Traceability App"
    assert trace["project"]["framework"] == "Angular"
    assert trace["component"]["name"] == "OrderComponent"
    assert trace["function_behavior"] == "submitOrder()"
    assert trace["strategy_id"] == "STRAT-ORDER-001"
    assert trace["edge_case_id"] == "EDGE-NETWORK-TIMEOUT"
