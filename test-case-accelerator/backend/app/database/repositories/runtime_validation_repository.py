from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models.runtime_validation import (
    RuntimeExecutionResult,
    RuntimeValidationRun,
    RuntimeValidationStatus,
)
from app.database.schema_validation import validate_database_schema


class RuntimeValidationRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create_run(
        self, *, project_id: uuid.UUID, source_stage_run_id: uuid.UUID,
        base_url: str,
    ) -> RuntimeValidationRun:
        # Re-check at the mutation boundary so alternate entry points cannot
        # write Stage 7 data without first validating the Alembic revision.
        validate_database_schema(self._session.connection())
        run = RuntimeValidationRun(
            project_id=project_id,
            source_stage_run_id=source_stage_run_id,
            base_url=base_url,
            execution_mode="unit_pytest",
        )
        self._session.add(run)
        self._commit(run)
        return run

    def get_by_id(self, run_id: uuid.UUID) -> RuntimeValidationRun | None:
        return self._session.get(RuntimeValidationRun, run_id)

    def get_latest_by_source_run_id(
        self, source_stage_run_id: uuid.UUID
    ) -> RuntimeValidationRun | None:
        return self._session.scalar(
            select(RuntimeValidationRun)
            .where(
                RuntimeValidationRun.source_stage_run_id
                == source_stage_run_id
            )
            .order_by(
                RuntimeValidationRun.created_at.desc(),
                RuntimeValidationRun.id.desc(),
            )
            .limit(1)
        )

    def mark_running(self, run: RuntimeValidationRun) -> None:
        run.status = RuntimeValidationStatus.RUNNING
        run.started_at = datetime.now(UTC)
        self._commit(run)

    def complete(
        self, run: RuntimeValidationRun, *, results: list[dict[str, Any]],
        summary: dict[str, Any], duration_ms: float,
    ) -> None:
        run.results.extend(RuntimeExecutionResult(run_id=run.id, **item) for item in results)
        run.summary = summary
        run.duration_ms = duration_ms
        run.status = (
            RuntimeValidationStatus.PARTIAL
            if summary.get("not_executable", 0) or summary.get("skipped", 0)
            else RuntimeValidationStatus.COMPLETED
        )
        run.finished_at = datetime.now(UTC)
        self._commit(run)

    def fail(self, run: RuntimeValidationRun, message: str) -> None:
        run.status = RuntimeValidationStatus.FAILED
        run.error_message = message
        run.finished_at = datetime.now(UTC)
        self._commit(run)

    def _commit(self, entity: RuntimeValidationRun) -> None:
        try:
            self._session.commit()
            self._session.refresh(entity)
        except SQLAlchemyError:
            self._session.rollback()
            raise
