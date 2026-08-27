import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError

from app.dependencies.security_scan import SecurityScanServiceDependency
from app.schemas.security_scan import SecurityFindingResponse, SecurityScanResponse
from app.services.security_scan import (
    SecurityScanError,
    SecurityScanRetryError,
    SecurityScanRunNotFoundError,
)

router = APIRouter(tags=["security scans"])


def _progress(status_value: str) -> int:
    return {
        "pending": 0,
        "running": 50,
        "completed": 100,
        "failed": 50,
    }.get(status_value, 0)


def _response(run) -> SecurityScanResponse:
    findings = []
    for finding in run.findings:
        metadata = finding.semgrep_metadata or {}
        findings.append(SecurityFindingResponse(
            id=finding.id,
            rule_id=finding.rule_id,
            severity=finding.severity,
            cwe=finding.cwe,
            owasp=finding.owasp,
            file=finding.file,
            line=finding.line,
            start_line=finding.line,
            end_line=metadata.get("_testforge_end_line", finding.line),
            confidence=metadata.get("_testforge_confidence"),
            category=metadata.get("_testforge_category"),
            code_snippet=metadata.get("_testforge_code_snippet"),
            message=finding.message,
            recommendation=metadata.get("_testforge_recommendation"),
            references=metadata.get("_testforge_references", []),
            duplicate_count=metadata.get("_testforge_duplicate_count", 1),
            semgrep_metadata=metadata,
        ))
    return SecurityScanResponse(
        run_id=run.id,
        project_id=run.project_id,
        status=run.status,
        progress_percent=_progress(run.status),
        summary=run.summary,
        error_message=run.error_message,
        retry_count=run.retry_count,
        created_at=run.created_at,
        started_at=run.started_at,
        finished_at=run.finished_at,
        findings=findings,
    )


@router.post(
    "/projects/{project_id}/security-scans",
    response_model=SecurityScanResponse,
    status_code=status.HTTP_201_CREATED,
)
def scan_project(
    project_id: uuid.UUID, service: SecurityScanServiceDependency
) -> SecurityScanResponse:
    try:
        run = service.run(project_id)
    except SecurityScanError as error:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(error)) from error
    except (OSError, SQLAlchemyError) as error:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR, "Security scan failed"
        ) from error
    if run is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")
    return _response(run)


@router.get("/security-scan-runs/{run_id}", response_model=SecurityScanResponse)
def get_scan(
    run_id: uuid.UUID, service: SecurityScanServiceDependency
) -> SecurityScanResponse:
    run = service.get_run(run_id)
    if run is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Security scan run not found")
    return _response(run)


@router.get(
    "/projects/{project_id}/security-scan-runs/latest",
    response_model=SecurityScanResponse,
)
def get_latest_scan(
    project_id: uuid.UUID, service: SecurityScanServiceDependency
) -> SecurityScanResponse:
    run = service.get_latest_run(project_id)
    if run is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Security scan run not found")
    return _response(run)


@router.post(
    "/security-scan-runs/{run_id}/retry", response_model=SecurityScanResponse
)
def retry_scan(
    run_id: uuid.UUID, service: SecurityScanServiceDependency
) -> SecurityScanResponse:
    try:
        return _response(service.retry(run_id))
    except SecurityScanRunNotFoundError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error
    except SecurityScanRetryError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error
    except SecurityScanError as error:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(error)) from error
    except SQLAlchemyError as error:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, "Database operation failed"
        ) from error
    except OSError as error:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR, "Security scan failed"
        ) from error
