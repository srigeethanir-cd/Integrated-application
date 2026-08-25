"""Application-level orchestration for the complete workflow."""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
import time

from app.database.models.code_understanding import CodeUnderstandingRun
from app.database.models.dependency import DependencyRun
from app.database.models.project import Project
from app.database.models.security_scan import SecurityScanRun
from app.services.code_understanding.code_understanding_service import (
    CodeUnderstandingService,
)
from app.services.dependency.dependency_service import DependencyService
from app.services.security_scan import SecurityScanService


class WorkflowError(RuntimeError):
    """Raised when a workflow stage does not produce its required artifact."""


@dataclass(frozen=True)
class WorkflowResult:
    project: Project
    current_stage: str = "stage_1"
    status: str = "waiting_for_approval"
    completed_stage: str | None = "stage_1"
    next_stage: str | None = "stage_2"
    security_scan_run: SecurityScanRun | None = None
    dependency_run: DependencyRun | None = None
    code_understanding_run: CodeUnderstandingRun | None = None
    test_generation: dict | None = None
    error: str | None = None
    logs: tuple[str, ...] = ()


class WorkflowService:
    """Continue an ingested Stage 1 project through Stages 2-5."""

    def __init__(
        self,
        dependency_service: DependencyService,
        security_scan_service: SecurityScanService,
        code_understanding_service: CodeUnderstandingService,
    ) -> None:
        self._dependency_service = dependency_service
        self._security_scan_service = security_scan_service
        self._code_understanding_service = code_understanding_service

    def run(self, project: Project) -> WorkflowResult:
        security_scan_run, dependency_run = self._run_discovery_branches(project.id)
        if dependency_run is None:
            raise WorkflowError("Project was not available for dependency discovery")
        if security_scan_run is None:
            raise WorkflowError("Project was not available for security scanning")
        code_understanding_run = self._code_understanding_service.run(
            project.id, dependency_run.id
        )
        return WorkflowResult(
            project=project,
            current_stage="stage_3",
            completed_stage="stage_3",
            next_stage=None,
            security_scan_run=security_scan_run,
            dependency_run=dependency_run,
            code_understanding_run=code_understanding_run,
        )

    def start(self, project: Project) -> WorkflowResult:
        """Return the persisted Stage 1 artifact without starting Stage 2."""
        return WorkflowResult(project=project)

    def run_through_stage_four(self, project: Project) -> WorkflowResult:
        """Run automatic preprocessing and pause at the Stage 4 approval gate."""
        transition = "stage_1"
        while True:
            try:
                result = self.continue_from(project, transition)
            except Exception:
                persisted = self.state(project)
                if persisted.status == "failed":
                    return persisted
                raise
            if result.status == "failed" or result.current_stage == "stage_4":
                return result
            transition = result.current_stage

    def continue_from(self, project: Project, from_stage: str) -> WorkflowResult:
        """Execute exactly one approved stage through the current Stage 3 scope."""
        state = self.state(project)
        if from_stage == "stage_1":
            if state.current_stage not in {"stage_1", "stage_2"}:
                raise WorkflowError("Stage 2 has already completed")
            if state.current_stage == "stage_2" and state.status != "failed":
                raise WorkflowError("Stage 2 has already completed or is running")
            security_scan_run, dependency_run = self._run_stage_two(
                project.id, state, retry=True
            )
            if dependency_run is None or security_scan_run is None:
                raise WorkflowError("Stage 2 did not produce its required artifacts")
            return WorkflowResult(
                project=project,
                current_stage="stage_2",
                completed_stage="stage_2",
                next_stage="stage_3",
                security_scan_run=security_scan_run,
                dependency_run=dependency_run,
                logs=(
                    "Stage 1 completed",
                    "Stage 2 dependency discovery completed",
                    "Stage 2 security scan completed",
                    "Waiting for approval before Stage 3",
                ),
            )
        if from_stage == "stage_2":
            if state.current_stage == "stage_3" and state.status != "failed":
                raise WorkflowError("Stage 3 has already completed or is running")
            if (
                state.dependency_run is None
                or state.dependency_run.status != "completed"
                or state.security_scan_run is None
                or state.security_scan_run.status != "completed"
            ):
                raise WorkflowError("Stage 2 must complete before Stage 3")
            run = self._code_understanding_service.understand(
                project.id, state.dependency_run.id
            )
            return WorkflowResult(
                project=project,
                current_stage="stage_3",
                completed_stage="stage_3",
                next_stage="stage_4",
                security_scan_run=state.security_scan_run,
                dependency_run=state.dependency_run,
                code_understanding_run=run,
                logs=("Stage 3 completed", "Waiting for approval"),
            )
        if from_stage == "stage_3":
            retrying_stage_four = (
                state.current_stage == "stage_4" and state.status == "failed"
            )
            if state.code_understanding_run is None or (
                not retrying_stage_four
                and getattr(
                    state.code_understanding_run.status,
                    "value",
                    state.code_understanding_run.status,
                ) != "completed"
            ):
                raise WorkflowError("Stage 3 must complete before Stage 4")
            existing = (state.code_understanding_run.result or {}).get(
                "test_generation"
            )
            if existing is not None:
                raise WorkflowError("Stage 4 has already completed")
            started = time.perf_counter()
            if state.current_stage == "stage_4" and state.status == "failed":
                generation = self._code_understanding_service.retry_test_generation(
                    project.id, state.code_understanding_run.id
                )
            else:
                generation = self._code_understanding_service.generate_test_cases(
                    project.id, state.code_understanding_run.id
                )
            duration_ms = round((time.perf_counter() - started) * 1000)
            return WorkflowResult(
                project=project,
                current_stage="stage_4",
                status="waiting_for_approval",
                completed_stage="stage_4",
                next_stage=None,
                security_scan_run=state.security_scan_run,
                dependency_run=state.dependency_run,
                code_understanding_run=state.code_understanding_run,
                test_generation=generation,
                logs=(
                    "Stage 1 completed",
                    "Stage 2 dependency discovery and security scan completed",
                    "Stage 3 code understanding completed",
                    "Stage 4 test generation completed",
                    f"Stage 4 generation duration: {duration_ms} ms",
                    "Waiting for approval before Stage 5",
                ),
            )
        raise WorkflowError("The requested stage transition is not supported")

    def state(self, project: Project) -> WorkflowResult:
        """Reconstruct approval state exclusively from persisted stage artifacts."""
        dependency_run = self._dependency_service.get_latest_workflow_run(project.id)
        security_scan_run = self._security_scan_service.get_latest_run(project.id)
        understanding_run = self._code_understanding_service.get_latest_workflow_run(
            project.id
        )
        if understanding_run is not None:
            failed = getattr(
                understanding_run.status, "value", understanding_run.status
            ) == "failed"
            generation = (understanding_run.result or {}).get("test_generation")
            if generation is not None:
                return WorkflowResult(
                    project=project,
                    current_stage="stage_4",
                    status="waiting_for_approval",
                    completed_stage="stage_4",
                    next_stage=None,
                    security_scan_run=security_scan_run,
                    dependency_run=dependency_run,
                    code_understanding_run=understanding_run,
                    test_generation=generation,
                    logs=(
                        "Stage 1 completed",
                        "Stage 2 dependency discovery and security scan completed",
                        "Stage 3 code understanding completed",
                        "Stage 4 test generation completed",
                        "Stage 4 generation duration: Not Available",
                        "Waiting for approval before Stage 5",
                    ),
                )
            if failed and understanding_run.failed_stage == "stage_4":
                return WorkflowResult(
                    project=project,
                    current_stage="stage_4",
                    status="failed",
                    completed_stage="stage_3",
                    next_stage=None,
                    security_scan_run=security_scan_run,
                    dependency_run=dependency_run,
                    code_understanding_run=understanding_run,
                    error=understanding_run.failure_reason,
                    logs=(understanding_run.failure_reason,)
                    if understanding_run.failure_reason else (),
                )
            return WorkflowResult(
                project=project,
                current_stage="stage_3",
                status="failed" if failed else "waiting_for_approval",
                completed_stage=None if failed else "stage_3",
                next_stage="stage_4" if not failed else None,
                security_scan_run=security_scan_run,
                dependency_run=dependency_run,
                code_understanding_run=understanding_run,
                error=understanding_run.failure_reason if failed else None,
                logs=(understanding_run.failure_reason,) if failed and understanding_run.failure_reason else (),
            )
        if dependency_run is not None or security_scan_run is not None:
            failed_runs = [
                run for run in (dependency_run, security_scan_run)
                if run is not None and run.status == "failed"
            ]
            complete = (
                dependency_run is not None
                and dependency_run.status == "completed"
                and security_scan_run is not None
                and security_scan_run.status == "completed"
            )
            error = next(
                (getattr(run, "error_message", None) for run in failed_runs
                 if getattr(run, "error_message", None)),
                "Stage 2 failed" if failed_runs else None,
            )
            return WorkflowResult(
                project=project,
                current_stage="stage_2",
                status=(
                    "failed" if failed_runs else
                    "waiting_for_approval" if complete else "running"
                ),
                completed_stage="stage_2" if complete else None,
                next_stage="stage_3" if complete else None,
                security_scan_run=security_scan_run,
                dependency_run=dependency_run,
                error=error,
                logs=(error,) if error else (
                    (
                        "Stage 1 completed",
                        "Stage 2 dependency discovery completed",
                        "Stage 2 security scan completed",
                        "Waiting for approval before Stage 3",
                    )
                    if complete else ()
                ),
            )
        return self.start(project)

    def _run_stage_two(
        self,
        project_id,
        state: WorkflowResult,
        *,
        retry: bool,
    ) -> tuple[SecurityScanRun | None, DependencyRun | None]:
        dependency_run = state.dependency_run
        security_run = state.security_scan_run
        dependency_complete = (
            dependency_run is not None and dependency_run.status == "completed"
        )
        security_complete = (
            security_run is not None and security_run.status == "completed"
        )
        if not dependency_complete and not security_complete:
            return self._run_discovery_branches(
                project_id, resume_security=retry
            )
        if not dependency_complete:
            dependency_run = self._dependency_service.run(project_id)
        if not security_complete:
            security_run = self._security_scan_service.run(
                project_id, resume_failed=retry
            )
        return security_run, dependency_run

    def resume(
        self,
        project: Project,
        *,
        start_stage: str | None = None,
        force: bool = False,
    ) -> WorkflowResult:
        import logging
        logger = logging.getLogger(__name__)
        logger.info("Pipeline resumed.")
        logger.info("Skipping completed Stage 1.")
        
        state = self._code_understanding_service.get_latest_pipeline_state(project.id)
        dependency_run = state.get("dependency_run")
        security_scan_run = self._security_scan_service.get_latest_run(project.id)

        dependency_complete = (
            dependency_run is not None and dependency_run.status == "completed"
        )
        security_complete = (
            security_scan_run is not None and security_scan_run.status == "completed"
        )
        if dependency_complete:
            logger.info("Skipping completed Dependency Discovery.")
        if security_complete:
            logger.info("Skipping completed Security Scan.")

        if not dependency_complete and not security_complete:
            security_scan_run, dependency_run = self._run_discovery_branches(
                project.id, resume_security=True
            )
        elif not dependency_complete:
            dependency_run = self._dependency_service.run(project.id)
        elif not security_complete:
            security_scan_run = self._security_scan_service.run(
                project.id, resume_failed=True
            )

        if dependency_run is None:
            raise WorkflowError("Project was not available for dependency discovery")
        if security_scan_run is None:
            raise WorkflowError("Project was not available for security scanning")

        if force:
            if start_stage != "test_generation":
                raise WorkflowError(
                    "Forced resume currently requires start_stage=test_generation"
                )
            code_understanding_run = (
                self._code_understanding_service.force_rerun(
                    project.id,
                    dependency_run.id,
                    start_stage=start_stage,
                )
            )
        elif start_stage is not None:
            raise WorkflowError("start_stage requires force=true")
        else:
            code_understanding_run = self._code_understanding_service.run(
                project.id, dependency_run.id
            )
        return WorkflowResult(
            project=project,
            current_stage="stage_3",
            completed_stage="stage_3",
            next_stage=None,
            security_scan_run=security_scan_run,
            dependency_run=dependency_run,
            code_understanding_run=code_understanding_run,
        )

    def _run_discovery_branches(
        self, project_id, *, resume_security: bool = False
    ) -> tuple[SecurityScanRun | None, DependencyRun | None]:
        # DependencyService is backed by the request-scoped SQLAlchemy session.
        # Keep it on the request thread and give the independent security service
        # (which owns its own session) the worker thread.
        with ThreadPoolExecutor(
            max_workers=1, thread_name_prefix="pipeline-security"
        ) as executor:
            security_future = executor.submit(
                self._security_scan_service.run,
                project_id,
                resume_failed=resume_security,
            )
            dependency_run = self._dependency_service.run(project_id)
            security_run = security_future.result()
        return security_run, dependency_run
