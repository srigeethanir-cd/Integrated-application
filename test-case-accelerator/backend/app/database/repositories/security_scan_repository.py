from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database.models.security_scan import SecurityFinding, SecurityScanRun


class SecurityScanRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, project_id: uuid.UUID) -> SecurityScanRun:
        run = SecurityScanRun(
            project_id=project_id, status="running", started_at=datetime.now(UTC)
        )
        self._session.add(run)
        self._commit(run)
        return run

    def get_by_id(self, run_id: uuid.UUID) -> SecurityScanRun | None:
        return self._session.get(SecurityScanRun, run_id)

    def get_by_id_for_update(self, run_id: uuid.UUID) -> SecurityScanRun | None:
        return self._session.scalar(
            select(SecurityScanRun)
            .where(SecurityScanRun.id == run_id)
            .with_for_update()
        )

    def get_latest_by_project_id(
        self, project_id: uuid.UUID
    ) -> SecurityScanRun | None:
        return self._session.scalar(
            select(SecurityScanRun)
            .where(SecurityScanRun.project_id == project_id)
            .order_by(SecurityScanRun.created_at.desc(), SecurityScanRun.id.desc())
            .limit(1)
        )

    def prepare_retry(self, run: SecurityScanRun) -> None:
        run.status = "running"
        run.retry_count += 1
        run.error_message = None
        run.started_at = datetime.now(UTC)
        run.finished_at = None
        run.findings.clear()
        self._commit(run)

    def complete(
        self, run: SecurityScanRun, findings: list[dict], summary: dict
    ) -> None:
        run.findings.extend(
            SecurityFinding(
                **{key: value for key, value in finding.items() if key != "metadata"},
                semgrep_metadata=finding["metadata"],
            )
            for finding in findings
        )
        run.summary = summary
        run.status = "completed"
        run.finished_at = datetime.now(UTC)
        self._commit(run)

    def fail(
        self,
        run: SecurityScanRun,
        message: str,
        *,
        summary: dict | None = None,
    ) -> None:
        run.status = "failed"
        run.error_message = message[:2_000]
        run.summary = summary
        run.finished_at = datetime.now(UTC)
        self._commit(run)

    def _commit(self, run: SecurityScanRun) -> None:
        try:
            self._session.commit()
            self._session.refresh(run)
        except SQLAlchemyError:
            self._session.rollback()
            raise
