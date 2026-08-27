import io
import uuid
import zipfile
from datetime import UTC, datetime
from unittest.mock import Mock

from app.database.models.runtime_validation import RuntimeValidationStatus
from app.dependencies.project import get_upload_service
from app.dependencies.runtime_validation import get_runtime_validation_service
from app.main import app
from app.schemas.runtime_validation import RuntimeValidationReport


def _zip() -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        archive.writestr("main.py", "from fastapi import FastAPI\napp = FastAPI()")
    return output.getvalue()


def test_upload_then_runtime_validation_persists_and_reports(client, project_factory) -> None:
    project = project_factory()
    upload = Mock()
    upload.upload_project.return_value = project
    app.dependency_overrides[get_upload_service] = lambda: upload
    uploaded = client.post(
        "/projects/upload",
        data={"name": "Runtime sample"},
        files={"uploaded_file": ("sample.zip", _zip(), "application/zip")},
    )
    assert uploaded.status_code == 201

    now = datetime.now(UTC)
    run_id, source_id = uuid.uuid4(), uuid.uuid4()
    run = Mock(
        id=run_id, project_id=project.id, source_stage_run_id=source_id,
        status=RuntimeValidationStatus.COMPLETED, execution_mode="managed",
        base_url="http://127.0.0.1:8001", duration_ms=12.5,
        summary={"passed": 1, "failed": 0, "skipped": 0, "not_executable": 0, "total": 1, "pass_rate": 100},
        error_message=None, created_at=now, started_at=now, finished_at=now,
    )
    report = RuntimeValidationReport(
        run_id=run_id, project_id=project.id, source_stage_run_id=source_id,
        status="completed", summary=run.summary, pass_rate=100,
        duration_ms=12.5, failed_tests=[], skipped_tests=[], results=[{
            "test_case_id": "TC-1", "runtime_status": "Passed",
            "expected_result": {"status_code": 200},
            "actual_result": {"status_code": 200}, "execution_time_ms": 5,
        }],
    )
    service = Mock()
    service.run.return_value = run
    service.get_run.return_value = run
    service.get_report.return_value = report
    app.dependency_overrides[get_runtime_validation_service] = lambda: service

    created = client.post(
        f"/projects/{project.id}/runtime-validation",
        json={"code_understanding_run_id": str(source_id)},
    )
    fetched = client.get(f"/runtime-validations/{run_id}")
    reported = client.get(f"/runtime-validations/{run_id}/report")

    assert created.status_code == 201
    assert fetched.json()["status"] == "completed"
    assert reported.status_code == 200
    assert reported.json()["results"][0]["runtime_status"] == "Passed"
    assert service.run.call_args.kwargs["base_url"] == (
        "http://127.0.0.1:8001"
    )
    service.get_report.assert_called_once_with(run_id)


def test_runtime_validation_report_preserves_preparation_failures(
    client, project_factory,
) -> None:
    project = project_factory()
    run_id, source_id = uuid.uuid4(), uuid.uuid4()
    summary = {
        "passed": 1, "failed": 0, "skipped": 0, "not_executable": 1,
        "runtime_preparation_failures": 1, "total": 2, "pass_rate": 50,
    }
    report = RuntimeValidationReport(
        run_id=run_id, project_id=project.id,
        source_stage_run_id=source_id, status="completed",
        summary=summary, pass_rate=50, duration_ms=10,
        failed_tests=[], skipped_tests=["TC-SKIP"], results=[
            {
                "test_case_id": "TC-RUN", "runtime_status": "Passed",
                "expected_result": {"status_code": 200},
                "actual_result": {"status_code": 200},
                "execution_time_ms": 2,
            },
            {
                "test_case_id": "TC-SKIP",
                "runtime_status": "NotExecutable",
                "expected_result": {
                    "source": "Runtime Preparation",
                    "issues": [{
                        "code": "route_unresolved",
                        "message": "No route",
                    }],
                },
                "actual_result": None,
                "assertion_failure": "No route",
                "execution_time_ms": 0,
            },
        ],
    )
    service = Mock()
    service.get_report.return_value = report
    app.dependency_overrides[get_runtime_validation_service] = lambda: service

    response = client.get(f"/runtime-validations/{run_id}/report")

    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"]["runtime_preparation_failures"] == 1
    assert payload["results"][1]["expected_result"]["source"] == (
        "Runtime Preparation"
    )
    assert payload["failed_tests"] == []
    assert payload["skipped_tests"] == ["TC-SKIP"]


def test_runtime_validation_report_serializes_http_500_sut_traceback(
    client, project_factory,
) -> None:
    project = project_factory()
    run_id, source_id = uuid.uuid4(), uuid.uuid4()
    diagnostic = (
        "Expected HTTP 404, got 500\n\n"
        "SUT traceback:\nTraceback (most recent call last):\n"
        "RuntimeError: observable SUT failure"
    )
    report = RuntimeValidationReport(
        run_id=run_id,
        project_id=project.id,
        source_stage_run_id=source_id,
        status="completed",
        summary={"passed": 0, "failed": 1, "total": 1, "pass_rate": 0},
        pass_rate=0,
        duration_ms=10,
        failed_tests=["TC-500"],
        skipped_tests=[],
        results=[{
            "test_case_id": "TC-500",
            "runtime_status": "Failed",
            "expected_result": {"status_code": 404},
            "actual_result": {
                "status_code": 500,
                "body": "Internal Server Error",
            },
            "assertion_failure": diagnostic,
            "logs": diagnostic,
            "execution_time_ms": 2,
        }],
    )
    service = Mock()
    service.get_report.return_value = report
    app.dependency_overrides[get_runtime_validation_service] = lambda: service

    response = client.get(f"/runtime-validations/{run_id}/report")

    assert response.status_code == 200
    result = response.json()["results"][0]
    assert "RuntimeError: observable SUT failure" in result["logs"]
    assert "RuntimeError: observable SUT failure" in result["assertion_failure"]
