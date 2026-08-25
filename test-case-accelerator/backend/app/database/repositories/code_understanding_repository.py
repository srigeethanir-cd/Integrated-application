"""Persistence operations for Stage 3 code-understanding runs."""

import uuid
import logging
import time
from copy import deepcopy
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models.code_understanding import (
    CodeUnderstandingRun,
    CodeUnderstandingStatus,
)
from app.database.retry import (
    MAX_DATABASE_RETRIES,
    is_transient_database_error,
    retry_delay,
)

logger = logging.getLogger(__name__)


class CodeUnderstandingRepository:
    """Manage persistence and state transitions for Stage 3 runs."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create_run(
        self,
        project_id: uuid.UUID,
        dependency_run_id: uuid.UUID,
        model_name: str,
        prompt_version: str,
    ) -> CodeUnderstandingRun:
        run = CodeUnderstandingRun(
            project_id=project_id,
            dependency_run_id=dependency_run_id,
            model_name=model_name,
            prompt_version=prompt_version,
            status=CodeUnderstandingStatus.PENDING,
        )
        self._session.add(run)
        self._commit_and_refresh(run)
        return run

    def get_by_id(
        self,
        run_id: uuid.UUID,
    ) -> CodeUnderstandingRun | None:
        return self._session.get(CodeUnderstandingRun, run_id)

    def get_by_project_id(
        self,
        project_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> list[CodeUnderstandingRun]:
        statement = (
            select(CodeUnderstandingRun)
            .where(CodeUnderstandingRun.project_id == project_id)
            .order_by(
                CodeUnderstandingRun.created_at.desc(),
                CodeUnderstandingRun.id,
            )
            .offset(skip)
            .limit(limit)
        )
        return list(self._session.scalars(statement).all())

    def get_by_dependency_run_id(
        self,
        dependency_run_id: uuid.UUID,
    ) -> list[CodeUnderstandingRun]:
        statement = (
            select(CodeUnderstandingRun)
            .where(
                CodeUnderstandingRun.dependency_run_id == dependency_run_id
            )
            .order_by(
                CodeUnderstandingRun.created_at.desc(),
                CodeUnderstandingRun.id,
            )
        )
        return list(self._session.scalars(statement).all())

    def get_latest_completed_by_project_id(
        self,
        project_id: uuid.UUID,
    ) -> CodeUnderstandingRun | None:
        statement = (
            select(CodeUnderstandingRun)
            .where(
                CodeUnderstandingRun.project_id == project_id,
                CodeUnderstandingRun.status == CodeUnderstandingStatus.COMPLETED,
            )
            .order_by(
                CodeUnderstandingRun.created_at.desc(),
                CodeUnderstandingRun.id.desc(),
            )
            .limit(1)
        )
        return self._session.scalar(statement)

    def get_latest_by_project_id(
        self, project_id: uuid.UUID
    ) -> CodeUnderstandingRun | None:
        statement = (
            select(CodeUnderstandingRun)
            .where(CodeUnderstandingRun.project_id == project_id)
            .order_by(
                CodeUnderstandingRun.created_at.desc(),
                CodeUnderstandingRun.id.desc(),
            )
            .limit(1)
        )
        return self._session.scalar(statement)

    def mark_running(
        self,
        run: CodeUnderstandingRun,
    ) -> CodeUnderstandingRun:
        run.status = CodeUnderstandingStatus.RUNNING
        run.started_at = datetime.now(UTC)
        run.finished_at = None
        run.error_message = None
        self._commit_and_refresh(run)
        return run

    def prepare_retry(self, run: CodeUnderstandingRun) -> CodeUnderstandingRun:
        """Increment retry metadata while retaining every completed artifact."""
        result = dict(run.result or {})
        invalidated = {
            "stage_4": (
                "test_generation", "test_verification",
                "quality_evaluation", "quality_optimization",
                "quality_checkpoint", "runtime_execution_plan",
            ),
            "stage_5": (
                "test_verification", "quality_evaluation",
                "quality_optimization", "quality_checkpoint",
                "runtime_execution_plan",
            ),
            "stage_6": (
                "quality_evaluation", "quality_optimization",
                "runtime_execution_plan",
            ),
            "runtime_preparation": ("runtime_execution_plan",),
        }
        if run.failed_stage == "stage_3" and run.last_successful_stage is None:
            result = {}
        else:
            for key in invalidated.get(run.failed_stage or "", ()):
                result.pop(key, None)
        run.result = result or None
        run.retry_count += 1
        run.status = CodeUnderstandingStatus.RUNNING
        run.started_at = datetime.now(UTC)
        run.finished_at = None
        run.error_message = None
        self._commit_and_refresh(run, method="prepare_retry")
        return run

    def prepare_forced_rerun(
        self, run: CodeUnderstandingRun, *, start_stage: str
    ) -> CodeUnderstandingRun:
        """Atomically invalidate a completed stage and every downstream artifact."""
        invalidated = {
            "stage_4": (
                "test_generation", "test_verification",
                "quality_evaluation", "quality_optimization",
                "quality_checkpoint", "runtime_execution_plan",
            ),
        }
        keys = invalidated.get(start_stage)
        if keys is None:
            raise ValueError(f"Unsupported forced rerun stage: {start_stage}")
        result = dict(run.result or {})
        for key in keys:
            result.pop(key, None)
        run.result = result
        run.status = CodeUnderstandingStatus.RUNNING
        run.started_at = datetime.now(UTC)
        run.finished_at = None
        run.error_message = None
        run.failed_stage = None
        run.failure_reason = None
        run.last_successful_stage = "stage_3"
        self._commit_and_refresh(run, method="prepare_forced_rerun")
        return run

    def prepare_artifact_regeneration(
        self, run: CodeUnderstandingRun
    ) -> CodeUnderstandingRun:
        """Atomically clear stale artifacts and return a completed run to RUNNING."""
        run.result = None
        run.status = CodeUnderstandingStatus.RUNNING
        run.started_at = datetime.now(UTC)
        run.finished_at = None
        run.error_message = None
        run.failed_stage = None
        run.failure_reason = None
        run.last_successful_stage = None
        self._commit_and_refresh(run, method="prepare_artifact_regeneration")
        return run

    def mark_stage_completed(
        self, run: CodeUnderstandingRun, stage: str
    ) -> CodeUnderstandingRun:
        run.last_successful_stage = stage
        self._commit_and_refresh(run, method="mark_stage_completed")
        return run

    def complete(
        self,
        run: CodeUnderstandingRun,
        result: dict[str, Any],
    ) -> CodeUnderstandingRun:
        run.status = CodeUnderstandingStatus.COMPLETED
        run.result = result
        run.finished_at = datetime.now(UTC)
        run.error_message = None
        self._commit_and_refresh(run)
        return run

    def save_quality_optimization(
        self,
        run: CodeUnderstandingRun,
        optimization: dict[str, Any],
    ) -> CodeUnderstandingRun:
        """Atomically persist Stage 4-6 optimization without replacing Stage 3 data."""
        result = dict(run.result or {})
        self._version_artifact(result, "quality_optimization", optimization)
        result.update(
            {
                "test_generation": optimization["test_generation"],
                "test_verification": optimization["test_verification"],
                "quality_evaluation": optimization["quality_evaluation"],
                "quality_optimization": optimization,
            }
        )
        if optimization.get("processing_status") != "partial_success":
            result.pop("quality_checkpoint", None)
        run.result = result
        run.last_successful_stage = "stage_6"
        self._commit_and_refresh(run, method="save_quality_optimization")
        return run

    def save_quality_checkpoint(
        self, run: CodeUnderstandingRun, checkpoint: dict[str, Any]
    ) -> CodeUnderstandingRun:
        """Persist resumable Stage 6 progress without discarding completed stages."""
        result = dict(run.result or {})
        result["quality_checkpoint"] = checkpoint
        if checkpoint.get("generation") is not None:
            result["test_generation"] = checkpoint["generation"]
        if checkpoint.get("verification") is not None:
            result["test_verification"] = checkpoint["verification"]
        run.result = result
        self._commit_and_refresh(run, method="save_quality_checkpoint")
        return run

    def save_runtime_execution_plan(
        self,
        run: CodeUnderstandingRun,
        runtime_execution_plan: dict[str, Any],
    ) -> CodeUnderstandingRun:
        """Persist Runtime Preparation without replacing Stage 3-6 artifacts."""
        result = dict(run.result or {})
        self._version_artifact(result, "runtime_execution_plan", runtime_execution_plan)
        result["runtime_execution_plan"] = runtime_execution_plan
        run.result = result
        run.last_successful_stage = "runtime_preparation"
        self._commit_and_refresh(run, method="save_runtime_execution_plan")
        return run

    def save_test_generation(
        self,
        run: CodeUnderstandingRun,
        generation: dict[str, Any],
    ) -> CodeUnderstandingRun:
        """Persist Stage 4 and invalidate artifacts derived from an older suite."""
        result = dict(run.result or {})
        self._version_artifact(result, "test_generation", generation)
        result["test_generation"] = generation
        for key in (
            "test_verification",
            "quality_evaluation",
            "quality_optimization",
            "quality_checkpoint",
            "runtime_execution_plan",
        ):
            result.pop(key, None)
        run.result = result
        run.last_successful_stage = "stage_4"
        self._commit_and_refresh(run, method="save_test_generation")
        return run

    def save_test_verification(
        self,
        run: CodeUnderstandingRun,
        verification: dict[str, Any],
    ) -> CodeUnderstandingRun:
        """Persist Stage 5 without replacing Stage 3 or Stage 4 artifacts."""
        result = dict(run.result or {})
        self._version_artifact(result, "test_verification", verification)
        result["test_verification"] = verification
        result.pop("quality_evaluation", None)
        result.pop("quality_optimization", None)
        run.result = result
        run.last_successful_stage = "stage_5"
        self._commit_and_refresh(run, method="save_test_verification")
        return run

    @staticmethod
    def _version_artifact(
        result: dict[str, Any], stage: str, artifact: dict[str, Any]
    ) -> None:
        """Append an immutable JSON snapshot before updating the active pointer."""
        import hashlib
        import json

        versions = dict(result.get("artifact_versions") or {})
        history = list(versions.get(stage) or [])
        canonical = json.dumps(
            artifact, sort_keys=True, separators=(",", ":"), default=str
        )
        digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        if not history or history[-1].get("content_hash") != digest:
            history.append({
                "version": len(history) + 1,
                "content_hash": digest,
                "artifact": json.loads(canonical),
            })
        versions[stage] = history
        result["artifact_versions"] = versions

    def save_stage3_result(
        self,
        run: CodeUnderstandingRun,
        result: dict[str, Any],
    ) -> CodeUnderstandingRun:
        run.result = result
        run.last_successful_stage = "stage_3"
        self._commit_and_refresh(run, method="save_stage3_result")
        return run

    def fail(
        self,
        run: CodeUnderstandingRun,
        error_message: str,
        *,
        failed_stage: str | None = None,
    ) -> CodeUnderstandingRun:
        run.status = CodeUnderstandingStatus.FAILED
        # Retain run.result to support resume capability
        run.finished_at = datetime.now(UTC)
        run.error_message = error_message
        run.failure_reason = error_message
        run.failed_stage = failed_stage
        self._commit_and_refresh(run)
        return run

    def _commit_and_refresh(
        self, run: CodeUnderstandingRun, *, method: str = "state_transition"
    ) -> None:
        values = {
            column.key: deepcopy(getattr(run, column.key))
            for column in CodeUnderstandingRun.__mapper__.column_attrs
        }
        for retry in range(MAX_DATABASE_RETRIES + 1):
            try:
                self._session.commit()
                self._session.refresh(run)
                return
            except Exception as error:
                self._session.rollback()
                if (
                    not is_transient_database_error(error)
                    or retry >= MAX_DATABASE_RETRIES
                ):
                    logger.exception(
                        "Repository database failure method=%s "
                        "entity=CodeUnderstandingRun entity_id=%s retries=%d",
                        method,
                        values.get("id"),
                        retry,
                    )
                    raise
                self._dispose_invalid_connection()
                attempt = retry + 1
                delay = retry_delay(attempt)
                logger.warning(
                    "Transient database failure; retrying method=%s "
                    "entity=CodeUnderstandingRun entity_id=%s attempt=%d/%d "
                    "delay_seconds=%.2f error=%s",
                    method,
                    values.get("id"),
                    attempt,
                    MAX_DATABASE_RETRIES,
                    delay,
                    type(error).__name__,
                )
                for key, value in values.items():
                    setattr(run, key, deepcopy(value))
                self._session.add(run)
                time.sleep(delay)

    def _dispose_invalid_connection(self) -> None:
        try:
            bind = self._session.get_bind()
            engine = getattr(bind, "engine", bind)
            dispose = getattr(engine, "dispose", None)
            if callable(dispose):
                dispose(close=False)
        except Exception:
            logger.exception("Failed to dispose invalid database connection")
