import uuid
from unittest.mock import Mock

from openai import APIConnectionError

from app.agents.code_understanding.agent import CodeUnderstandingResult
from app.dependencies.code_understanding import get_code_understanding_service
from app.main import app
from app.services.code_understanding.code_understanding_service import (
    DependencyRunNotFoundError,
    DependencyRunNotReadyError,
    ProjectNotFoundError,
)
from app.agents.test_generation.test_generation_agent import (
    TestGenerationError as GenerationError,
)
from app.agents.semantic_verification.agent import (
    TestVerificationError as VerificationError,
)


def test_successful_understanding_run(client) -> None:
    project_id = uuid.uuid4()
    dependency_run_id = uuid.uuid4()
    run_id = uuid.uuid4()
    result = CodeUnderstandingResult(
        project_summary="Example project",
        architecture="Layered architecture",
    )
    service = Mock()
    service.understand.return_value = Mock(
        id=run_id,
        status="completed",
        result=result.model_dump(mode="json"),
    )
    app.dependency_overrides[get_code_understanding_service] = lambda: service

    response = client.post(
        f"/projects/{project_id}/understand",
        json={"dependency_run_id": str(dependency_run_id)},
    )

    assert response.status_code == 201
    assert response.json()["run_id"] == str(run_id)
    assert response.json()["status"] == "completed"
    assert response.json()["result"]["project_summary"] == "Example project"
    service.understand.assert_called_once_with(project_id, dependency_run_id)


def test_successful_understanding_includes_stage_five_result(client) -> None:
    run_id = uuid.uuid4()
    generated_case = {
        "id": "TC-1",
        "title": "Create project",
        "description": "Create a project",
        "category": "integration",
        "priority": "high",
        "severity": "major",
        "preconditions": [],
        "steps": ["POST /projects"],
        "expected_results": ["Project is returned"],
        "requirement_ids": [],
        "business_rule_ids": [],
        "traceability": None,
    }
    result = {
        "project_summary": "Example",
        "architecture": "Layered",
        "test_generation": {
            "generated_test_cases": [generated_case],
            "coverage_summary": {
                "requirement_coverage": 0.0,
                "category_coverage": 10.0,
            },
            "total_generated": 1,
            "total_after_deduplication": 1,
        },
        "test_verification": {
            "results": [
                {
                    "test_case_id": "TC-1",
                    "status": "Partial",
                    "confidence": 0.55,
                    "evidence": [],
                    "findings": [],
                }
            ],
            "summary": {"verified": 0, "partial": 1, "failed": 0},
            "total_verified": 0,
        },
    }
    service = Mock()
    service.run.return_value = Mock(id=run_id, status="completed", result=result)
    app.dependency_overrides[get_code_understanding_service] = lambda: service

    response = client.post(
        f"/projects/{uuid.uuid4()}/pipeline",
        json={"dependency_run_id": str(uuid.uuid4())},
    )

    assert response.status_code == 201
    assert (
        response.json()["result"]["test_verification"]["results"][0]["status"]
        == "Partial"
    )


def test_understanding_returns_not_found_for_invalid_project(client) -> None:
    service = Mock()
    service.understand.side_effect = ProjectNotFoundError("Project not found")
    app.dependency_overrides[get_code_understanding_service] = lambda: service

    response = client.post(
        f"/projects/{uuid.uuid4()}/understand",
        json={"dependency_run_id": str(uuid.uuid4())},
    )

    assert response.status_code == 404


def test_understanding_requires_completed_dependency_run(client) -> None:
    service = Mock()
    service.understand.side_effect = DependencyRunNotReadyError(
        "Dependency run must be completed before code understanding"
    )
    app.dependency_overrides[get_code_understanding_service] = lambda: service

    response = client.post(
        f"/projects/{uuid.uuid4()}/understand",
        json={"dependency_run_id": str(uuid.uuid4())},
    )

    assert response.status_code == 409


def test_understanding_returns_not_found_for_missing_dependency_run(client) -> None:
    service = Mock()
    service.understand.side_effect = DependencyRunNotFoundError(
        "Dependency run not found"
    )
    app.dependency_overrides[get_code_understanding_service] = lambda: service

    response = client.post(
        f"/projects/{uuid.uuid4()}/understand",
        json={"dependency_run_id": str(uuid.uuid4())},
    )

    assert response.status_code == 404


def test_understanding_maps_llm_failure_to_bad_gateway(client) -> None:
    service = Mock()
    service.understand.side_effect = APIConnectionError(request=Mock())
    app.dependency_overrides[get_code_understanding_service] = lambda: service

    response = client.post(
        f"/projects/{uuid.uuid4()}/understand",
        json={"dependency_run_id": str(uuid.uuid4())},
    )

    assert response.status_code == 502
    assert response.json() == {"detail": "Code-understanding provider failed"}


def test_understanding_maps_test_generation_failure_to_bad_gateway(client) -> None:
    service = Mock()
    service.run.side_effect = GenerationError("invalid provider response")
    app.dependency_overrides[get_code_understanding_service] = lambda: service

    response = client.post(
        f"/projects/{uuid.uuid4()}/pipeline",
        json={"dependency_run_id": str(uuid.uuid4())},
    )

    assert response.status_code == 502
    assert response.json() == {"detail": "Test-generation provider failed"}


def test_understanding_maps_test_verification_failure_to_bad_gateway(client) -> None:
    service = Mock()
    service.run.side_effect = VerificationError("invalid provider response")
    app.dependency_overrides[get_code_understanding_service] = lambda: service

    response = client.post(
        f"/projects/{uuid.uuid4()}/pipeline",
        json={"dependency_run_id": str(uuid.uuid4())},
    )

    assert response.status_code == 502
    assert response.json() == {"detail": "Test-verification provider failed"}


def test_generate_test_cases_endpoint_returns_stage_four_only(client) -> None:
    project_id = uuid.uuid4()
    run_id = uuid.uuid4()
    generated_case = {
        "id": "TC-1",
        "title": "Create project",
        "description": "Create a project",
        "category": "integration",
        "priority": "high",
        "severity": "major",
        "steps": ["POST /projects"],
        "expected_results": ["Project is returned"],
    }
    service = Mock()
    service.generate_test_cases.return_value = {
        "generated_test_cases": [generated_case],
        "coverage_summary": {
            "requirement_coverage": 0.0,
            "category_coverage": 10.0,
        },
        "total_generated": 1,
        "total_after_deduplication": 1,
    }
    app.dependency_overrides[get_code_understanding_service] = lambda: service

    response = client.post(
        f"/projects/{project_id}/generate-test-cases",
        json={"code_understanding_run_id": str(run_id)},
    )

    assert response.status_code == 200
    assert response.json()["generated_test_cases"][0]["id"] == "TC-1"
    assert "test_verification" not in response.json()
    service.generate_test_cases.assert_called_once_with(project_id, run_id)


def test_verify_test_cases_endpoint_returns_stage_five_only(client) -> None:
    project_id = uuid.uuid4()
    run_id = uuid.uuid4()
    test_case = {
        "id": "TC-1",
        "title": "Create project",
        "description": "Create a project",
        "category": "integration",
        "priority": "high",
        "severity": "major",
        "steps": ["POST /projects"],
        "expected_results": ["Project is returned"],
    }
    service = Mock()
    service.verify_test_cases.return_value = {
        "results": [
            {
                "test_case_id": "TC-1",
                "status": "Partial",
                "confidence": 0.5,
                "evidence": [],
                "findings": [],
            }
        ],
        "summary": {"verified": 0, "partial": 1, "failed": 0},
        "total_verified": 0,
    }
    app.dependency_overrides[get_code_understanding_service] = lambda: service

    response = client.post(
        f"/projects/{project_id}/verify-test-cases",
        json={
            "code_understanding_run_id": str(run_id),
            "test_cases": [test_case],
        },
    )

    assert response.status_code == 200
    assert response.json()["results"][0]["status"] == "Partial"
    supplied_case = service.verify_test_cases.call_args.args[2][0]
    assert supplied_case.id == "TC-1"


def test_openapi_exposes_independent_and_pipeline_routes(client) -> None:
    paths = client.get("/openapi.json").json()["paths"]

    assert "/projects/{project_id}/understand" in paths
    assert "/projects/{project_id}/generate-test-cases" in paths
    assert "/projects/{project_id}/verify-test-cases" in paths
    assert "/projects/{project_id}/pipeline" in paths
    assert "/projects/{project_id}/evaluate-test-quality" in paths
    assert "/projects/{project_id}/optimize-test-quality" in paths
    assert "/projects/{project_id}/pipeline-state" in paths
    assert "/projects/{project_id}/code-understanding-runs/latest" in paths
    assert "/projects/{project_id}/generated-test-cases/latest" in paths
    assert "/projects/{project_id}/verification-results/latest" in paths


def test_evaluate_test_quality_endpoint_returns_stage_six_result(client) -> None:
    project_id, run_id = uuid.uuid4(), uuid.uuid4()
    service = Mock()
    service.evaluate_test_quality.return_value = {
        "overall_score": 95,
        "dimension_scores": {
            "coverage": 95,
            "correctness": 95,
            "traceability": 95,
            "completeness": 95,
            "duplicates": 100,
            "maintainability": 95,
            "category_coverage": 90,
        },
        "recommendations": [],
        "feedback": {
            "weak_dimensions": [],
            "improve_test_case_ids": [],
            "replace_test_case_ids": [],
            "missing_categories": [],
            "instructions": [],
        },
        "threshold_met": True,
        "iteration": 1,
    }
    app.dependency_overrides[get_code_understanding_service] = lambda: service
    test_case = {
        "id": "TC-1",
        "title": "Test",
        "description": "Test",
        "category": "functional",
        "priority": "medium",
        "severity": "minor",
        "steps": ["Act"],
        "expected_results": ["Success"],
    }

    response = client.post(
        f"/projects/{project_id}/evaluate-test-quality",
        json={
            "code_understanding_run_id": str(run_id),
            "test_cases": [test_case],
            "verification": {
                "results": [
                    {
                        "test_case_id": "TC-1",
                        "status": "Verified",
                        "confidence": 0.9,
                        "evidence": [],
                        "findings": [],
                    }
                ],
                "summary": {"verified": 1, "partial": 0, "failed": 0},
                "total_verified": 1,
            },
        },
    )

    assert response.status_code == 200
    assert response.json()["overall_score"] == 95
    service.evaluate_test_quality.assert_called_once()


def test_get_latest_pipeline_state_restores_persisted_artifacts(client) -> None:
    project_id, dependency_run_id, understanding_run_id = (
        uuid.uuid4(),
        uuid.uuid4(),
        uuid.uuid4(),
    )
    generation = {
        "generated_test_cases": [],
        "coverage_summary": {},
        "total_generated": 0,
        "total_after_deduplication": 0,
        "generation_status": "complete",
        "uncovered_requirements": [],
    }
    verification = {
        "results": [],
        "summary": {"verified": 0, "partial": 0, "failed": 0},
        "total_verified": 0,
    }
    runtime_plan = {
        "targets": [],
        "issues": [],
        "total_tests": 0,
        "prepared_tests": 0,
        "unresolved_tests": 0,
    }
    understanding_result = {
        "project_summary": "Persisted project",
        "architecture": "Layered",
        "_artifact_version": {"composite": "internal"},
        "test_generation": generation,
        "test_verification": verification,
        "quality_checkpoint": {
            "best_score": 75.0,
            "processing_status": "in_progress",
        },
    }
    service = Mock()
    service.get_latest_pipeline_state.return_value = {
        "project_id": project_id,
        "dependency_run": Mock(
            id=dependency_run_id,
            project_id=project_id,
            project_path="/storage/project/source",
            status="completed",
            files=[],
        ),
        "understanding_run": Mock(
            id=understanding_run_id,
            status="completed",
            result=understanding_result,
        ),
        "test_generation": generation,
        "test_verification": verification,
        "quality_optimization": None,
        "runtime_execution_plan": runtime_plan,
    }
    app.dependency_overrides[get_code_understanding_service] = lambda: service

    response = client.get(f"/projects/{project_id}/pipeline-state")

    assert response.status_code == 200
    body = response.json()
    assert body["dependency"]["run_id"] == str(dependency_run_id)
    assert body["understanding"]["run_id"] == str(understanding_run_id)
    assert "quality_checkpoint" not in body["understanding"]["result"]
    assert "_artifact_version" not in body["understanding"]["result"]
    assert body["generation"] == generation
    assert body["verification"] == verification
    assert body["runtime_preparation"] == runtime_plan


def test_latest_artifact_endpoints_return_persisted_results(client) -> None:
    project_id, run_id = uuid.uuid4(), uuid.uuid4()
    generation = {
        "generated_test_cases": [],
        "coverage_summary": {},
        "total_generated": 0,
        "total_after_deduplication": 0,
        "generation_status": "complete",
        "uncovered_requirements": [],
    }
    verification = {
        "results": [],
        "summary": {"verified": 0, "partial": 0, "failed": 0},
        "total_verified": 0,
    }
    service = Mock()
    service.get_latest_run.return_value = Mock(
        id=run_id,
        status="completed",
        result={"project_summary": "Persisted", "architecture": "Layered"},
    )
    service.get_latest_pipeline_state.return_value = {
        "test_generation": generation,
        "test_verification": verification,
    }
    app.dependency_overrides[get_code_understanding_service] = lambda: service

    understanding = client.get(
        f"/projects/{project_id}/code-understanding-runs/latest"
    )
    generated = client.get(
        f"/projects/{project_id}/generated-test-cases/latest"
    )
    verified = client.get(
        f"/projects/{project_id}/verification-results/latest"
    )

    assert understanding.status_code == 200
    assert understanding.json()["run_id"] == str(run_id)
    assert generated.status_code == 200
    assert generated.json() == generation
    assert verified.status_code == 200
    assert verified.json() == verification
