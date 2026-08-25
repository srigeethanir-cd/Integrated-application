from app.agents.test_generation.lifecycle_detector import LifecycleDetector
from app.schemas.test_case import TestCase as Case


def test_detector_returns_no_lifecycle_behavior_for_regular_endpoint_artifacts() -> (
    None
):
    stage3 = {
        "entrypoints": [
            {
                "path": "app/api/projects.py",
                "symbol": "create_project",
                "purpose": "Create a project through an API endpoint",
            }
        ],
        "execution_flows": [
            {
                "name": "Create project",
                "entrypoint": "create_project",
                "steps": ["Validate input", "Persist project"],
                "files": ["app/api/projects.py"],
            }
        ],
    }

    assert LifecycleDetector().detect(stage3) == []


def test_detector_captures_supported_lifecycle_patterns() -> None:
    stage3 = {
        "entrypoints": [
            {
                "path": "app/main.py",
                "symbol": "create_app",
                "purpose": "FastAPI application factory",
            }
        ],
        "execution_flows": [
            {
                "name": "Application lifespan",
                "entrypoint": "lifespan",
                "steps": [
                    "Register routers using include_router",
                    "Initialize dependencies",
                    "Connect to the database",
                ],
                "files": ["app/main.py"],
            }
        ],
    }

    behavior_types = {item["type"] for item in LifecycleDetector().detect(stage3)}

    assert behavior_types == {
        "startup_event",
        "application_initialization",
        "router_registration",
        "dependency_initialization",
        "database_service_startup",
    }


def test_filter_removes_lifecycle_tests_without_stage_three_evidence() -> None:
    lifecycle_case = Case.model_validate(
        {
            "id": "TC-LIFE",
            "title": "Application startup succeeds",
            "description": "Verify the startup lifecycle",
            "category": "integration",
            "priority": "high",
            "severity": "major",
            "steps": ["Start the application"],
            "expected_results": ["Application is ready"],
        }
    )
    endpoint_case = lifecycle_case.model_copy(
        update={
            "id": "TC-API",
            "title": "Create project",
            "description": "POST a project",
            "steps": ["Submit POST /projects"],
            "expected_results": ["Project is returned"],
        }
    )

    assert LifecycleDetector().filter_supported(
        [lifecycle_case, endpoint_case], []
    ) == [endpoint_case]


def test_filter_keeps_lifecycle_tests_with_matching_evidence() -> None:
    lifecycle_case = Case.model_validate(
        {
            "id": "TC-LIFE",
            "title": "Application startup succeeds",
            "description": "Verify the startup lifecycle",
            "category": "integration",
            "priority": "high",
            "severity": "major",
            "steps": ["Start the application"],
            "expected_results": ["Application is ready"],
        }
    )

    assert LifecycleDetector().filter_supported(
        [lifecycle_case], [{"type": "startup_event"}]
    ) == [lifecycle_case]
