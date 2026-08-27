"""Persistence operations for dependency discovery runs."""

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database.models.dependency import DependencyRun
from app.database.models.discovered_file import DiscoveredFile
from app.schemas.file_metadata import FileMetadata


class DependencyRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create_run(self, project_id: uuid.UUID, project_path: str) -> DependencyRun:
        run = DependencyRun(
            project_id=project_id,
            project_path=project_path,
            status="running",
        )
        self._session.add(run)
        self._commit_and_refresh(run)
        return run

    def get_by_id(self, run_id: uuid.UUID) -> DependencyRun | None:
        return self._session.get(DependencyRun, run_id)

    def get_latest_completed_by_project_id(
        self,
        project_id: uuid.UUID,
    ) -> DependencyRun | None:
        statement = (
            select(DependencyRun)
            .where(
                DependencyRun.project_id == project_id,
                DependencyRun.status == "completed",
            )
            .order_by(DependencyRun.created_at.desc(), DependencyRun.id.desc())
            .limit(1)
        )
        return self._session.scalar(statement)

    def get_latest_by_project_id(
        self,
        project_id: uuid.UUID,
    ) -> DependencyRun | None:
        """Return the latest run regardless of status for workflow inspection."""
        statement = (
            select(DependencyRun)
            .where(DependencyRun.project_id == project_id)
            .order_by(DependencyRun.created_at.desc(), DependencyRun.id.desc())
            .limit(1)
        )
        return self._session.scalar(statement)

    def complete(self, run: DependencyRun, metadata: list[FileMetadata]) -> None:
        run.files.extend(
            DiscoveredFile(
                path=item.path,
                language=item.language,
                is_entry_point=item.is_entry_point,
                imports=item.imports,
                classes=item.classes,
                functions=item.functions,
            )
            for item in metadata
        )
        run.status = "completed"
        run.finished_at = datetime.now(UTC)
        self._commit_and_refresh(run)

    def fail(self, run: DependencyRun) -> None:
        run.status = "failed"
        run.finished_at = datetime.now(UTC)
        self._commit_and_refresh(run)

    def save_analysis_status(
        self,
        run_id: uuid.UUID,
        stage_number: int,
        step: str,
        status: str,
        error_message: str | None = None,
    ) -> None:
        from app.database.models.analysis_status import AnalysisStatus
        statement = (
            select(AnalysisStatus)
            .where(
                AnalysisStatus.run_id == run_id,
                AnalysisStatus.step == step,
            )
        )
        entry = self._session.scalar(statement)
        now = datetime.now(UTC)
        if entry is None:
            entry = AnalysisStatus(
                run_id=run_id,
                stage_number=stage_number,
                step=step,
                status=status,
                retry_count=0,
                started_at=now if status == "running" else None,
                completed_at=now if status == "completed" else None,
                error_message=error_message,
            )
            self._session.add(entry)
        else:
            if status == "running" and entry.status in ("failed", "completed"):
                entry.retry_count += 1
                entry.started_at = now
                entry.completed_at = None
            elif status == "completed":
                entry.completed_at = now
            
            entry.status = status
            entry.stage_number = stage_number
            if error_message is not None:
                entry.error_message = error_message
            entry.updated_at = now
        try:
            # Pipeline stage/result writes establish the durable transaction
            # boundaries; status rows only need to be visible in this transaction.
            self._session.flush()
        except SQLAlchemyError:
            self._session.rollback()
            raise

    def get_analysis_status(
        self,
        run_id: uuid.UUID,
        step: str,
    ) -> Any | None:
        from app.database.models.analysis_status import AnalysisStatus
        statement = (
            select(AnalysisStatus)
            .where(
                AnalysisStatus.run_id == run_id,
                AnalysisStatus.step == step,
            )
        )
        return self._session.scalar(statement)

    def _commit_and_refresh(self, run: DependencyRun) -> None:
        try:
            self._session.commit()
            self._session.refresh(run)
        except SQLAlchemyError:
            self._session.rollback()
            raise
