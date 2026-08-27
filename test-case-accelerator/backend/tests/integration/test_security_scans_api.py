import uuid
from datetime import UTC, datetime
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.database.models.security_scan import SecurityFinding, SecurityScanRun
from app.dependencies.security_scan import get_security_scan_service
from app.main import app
from app.services.security_scan import (
    SecurityScanError,
    SecurityScanRetryError,
    SecurityScanRunNotFoundError,
    SecurityScanService,
)


def _completed_run() -> SecurityScanRun:
    run = SecurityScanRun(
        id=uuid.uuid4(),
        project_id=uuid.uuid4(),
        status="completed",
        retry_count=1,
        created_at=datetime(2026, 7, 27, tzinfo=UTC),
        started_at=datetime(2026, 7, 27, tzinfo=UTC),
        finished_at=datetime(2026, 7, 27, tzinfo=UTC),
        summary={
            "total_findings": 1,
            "by_severity": {"ERROR": 1},
            "files_scanned": 3,
            "errors": 0,
            "warnings": 1,
            "parser_errors": 1,
            "diagnostics": [
                {
                    "level": "warning",
                    "category": "parser_error",
                    "type": "Parse error",
                    "message": "Could not parse one file",
                    "path": "broken.py",
                }
            ],
            "engine": "semgrep",
            "engine_version": "1.171.0",
            "duration_ms": 1250,
        },
    )
    run.findings = [
        SecurityFinding(
            id=uuid.uuid4(),
            rule_id="audit.python.eval",
            severity="ERROR",
            cwe=["CWE-95"],
            owasp=["A03:2021"],
            file="nested/vulnerable.py",
            line=2,
            message="Avoid dynamic eval",
            semgrep_metadata={"cwe": "CWE-95", "owasp": "A03:2021"},
        )
    ]
    return run


def test_latest_security_scan_returns_persisted_report(
    client: TestClient,
) -> None:
    run = _completed_run()
    service = MagicMock(spec=SecurityScanService)
    service.get_latest_run.return_value = run
    app.dependency_overrides[get_security_scan_service] = lambda: service

    response = client.get(
        f"/projects/{run.project_id}/security-scan-runs/latest"
    )

    assert response.status_code == 200
    report = response.json()
    assert report["status"] == "completed"
    assert report["progress_percent"] == 100
    assert report["summary"]["files_scanned"] == 3
    assert report["summary"]["errors"] == 0
    assert report["summary"]["warnings"] == 1
    assert report["summary"]["diagnostics"][0]["type"] == "Parse error"
    finding = report["findings"][0]
    assert finding["id"] == str(run.findings[0].id)
    assert finding["rule_id"] == "audit.python.eval"
    assert finding["severity"] == "ERROR"
    assert finding["cwe"] == ["CWE-95"]
    assert finding["owasp"] == ["A03:2021"]
    assert finding["file"] == "nested/vulnerable.py"
    assert finding["start_line"] == 2
    assert finding["end_line"] == 2
    assert finding["confidence"] is None
    assert finding["category"] is None
    assert finding["code_snippet"] is None
    assert finding["recommendation"] is None
    assert finding["references"] == []
    assert finding["duplicate_count"] == 1


def test_retry_security_scan_returns_same_run_with_retry_metadata(
    client: TestClient,
) -> None:
    run = _completed_run()
    service = MagicMock(spec=SecurityScanService)
    service.retry.return_value = run
    app.dependency_overrides[get_security_scan_service] = lambda: service

    response = client.post(f"/security-scan-runs/{run.id}/retry")

    assert response.status_code == 200
    assert response.json()["run_id"] == str(run.id)
    assert response.json()["retry_count"] == 1
    service.retry.assert_called_once_with(run.id)


def test_retry_security_scan_maps_domain_and_scanner_errors(
    client: TestClient,
) -> None:
    service = MagicMock(spec=SecurityScanService)
    app.dependency_overrides[get_security_scan_service] = lambda: service
    run_id = uuid.uuid4()

    for error, expected_status in (
        (SecurityScanRunNotFoundError("missing"), 404),
        (SecurityScanRetryError("not failed"), 409),
        (SecurityScanError("semgrep crashed"), 502),
    ):
        service.retry.side_effect = error
        response = client.post(f"/security-scan-runs/{run_id}/retry")
        assert response.status_code == expected_status
