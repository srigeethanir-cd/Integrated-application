"""Stage 7 direct pytest unit-test execution."""

from __future__ import annotations

import logging
import uuid

from app.database.models.code_understanding import CodeUnderstandingStatus
from app.database.models.runtime_validation import RuntimeValidationRun
from app.database.repositories.code_understanding_repository import CodeUnderstandingRepository
from app.database.repositories.project_repository import ProjectRepository
from app.database.repositories.runtime_validation_repository import RuntimeValidationRepository
from app.schemas.runtime_preparation import RuntimeExecutionPlan, RuntimeExecutionTarget
from app.schemas.runtime_validation import RuntimeValidationReport
from app.schemas.test_case import TestCase
from app.services.ingestion.storage_service import StorageService
from app.services.runtime.execution_manager import ExecutionManager
from app.services.runtime.openapi_metadata_service import OpenAPIMetadataService
from app.services.runtime.sut_backend_manager import (
    SUT_BASE_URL,
    SUTBackendManager,
)

logger = logging.getLogger(__name__)


class RuntimeValidationError(RuntimeError):
    pass


class RuntimeProjectNotFoundError(RuntimeValidationError):
    pass


class RuntimeSourceRunNotFoundError(RuntimeValidationError):
    pass


class RuntimeArtifactNotReadyError(RuntimeValidationError):
    pass


class RuntimeValidationRunNotFoundError(RuntimeValidationError):
    pass


class RuntimeValidationService:
    """Execute immutable Stage 6 unit contracts without starting an application."""

    def __init__(
        self,
        project_repository: ProjectRepository,
        code_repository: CodeUnderstandingRepository,
        runtime_repository: RuntimeValidationRepository,
        storage_service: StorageService,
        execution_manager: ExecutionManager,
        openapi_metadata_service: OpenAPIMetadataService | None = None,
        sut_backend_manager: SUTBackendManager | None = None,
    ) -> None:
        self._projects = project_repository
        self._code_runs = code_repository
        self._runtime_runs = runtime_repository
        self._storage = storage_service
        self._execution = execution_manager
        self._openapi = openapi_metadata_service or OpenAPIMetadataService()
        self._sut = sut_backend_manager or SUTBackendManager(self._openapi)

    def run(
        self, *, project_id: uuid.UUID,
        code_understanding_run_id: uuid.UUID | None,
        base_url: str, test_case_ids: list[str] | None,
        timeout_seconds: int,
    ) -> RuntimeValidationRun:
        project = self._projects.get_by_id(project_id)
        if project is None:
            raise RuntimeProjectNotFoundError("Project not found")
        source_run = (
            self._code_runs.get_by_id(code_understanding_run_id)
            if code_understanding_run_id is not None
            else self._code_runs.get_latest_completed_by_project_id(project_id)
        )
        if source_run is None:
            source_run = self._code_runs.get_latest_by_project_id(project_id)

        if source_run is None or source_run.project_id != project_id:
            raise RuntimeSourceRunNotFoundError("Stage 6 source run not found")

        if source_run.status not in (CodeUnderstandingStatus.COMPLETED, CodeUnderstandingStatus.FAILED, CodeUnderstandingStatus.RUNNING):
            raise RuntimeArtifactNotReadyError("Stage 6 source run is not completed")

        result = dict(source_run.result or {})
        project_directory = self._storage.resolve_project_directory(
            project_id, project.storage_path
        )
        source_directory = project_directory / "source"
        if not source_directory.is_dir():
            raise RuntimeArtifactNotReadyError("Project source directory does not exist")
        tests, failures, available_ids = self._runtime_inputs(result)
        if test_case_ids is not None:
            requested = set(test_case_ids)
            missing = requested - available_ids
            if missing:
                raise RuntimeArtifactNotReadyError(
                    f"Unknown test case IDs: {', '.join(sorted(missing))}"
                )
            selected_ids = self._dependency_closure(tests, requested)
            tests = [
                item for item in tests
                if self._test_case_id(item) in selected_ids
            ]
            failures = [item for item in failures if item["test_case_id"] in requested]

        logger.info(
            "Starting isolated unit runtime project_id=%s source=%s tests=%d",
            project_id, source_directory.resolve(), len(tests),
        )
        run = self._runtime_runs.create_run(
            project_id=project_id,
            source_stage_run_id=source_run.id,
            # Preserved transport field; no connection is made to this value.
            base_url=base_url.rstrip("/"),
        )
        try:
            self._runtime_runs.mark_running(run)
            http_targets = [
                item for item in tests
                if isinstance(item, RuntimeExecutionTarget)
                and item.classification == "HTTP"
            ]
            if http_targets:
                expected_endpoints = [
                    {"route": item.route, "method": item.http_method}
                    for item in http_targets
                    if item.route and item.http_method
                ]
                with self._sut.ensure_running(
                    source_directory,
                    expected_endpoints=expected_endpoints,
                    timeout_seconds=min(timeout_seconds, 30),
                ) as lease:
                    sut_url = getattr(lease, "base_url", SUT_BASE_URL)
                    completed, error = self._openapi.complete(
                        http_targets,
                        base_url=sut_url,
                        timeout_seconds=min(timeout_seconds, 15),
                        document=lease.document,
                    )
                    if error:
                        raise RuntimeArtifactNotReadyError(error)
                    by_id = {item.test_case_id: item for item in completed}
                    executable_tests = [
                        by_id.get(item.test_case_id, item)
                        if isinstance(item, RuntimeExecutionTarget) else item
                        for item in tests
                    ]
                    outcome = self._execution.execute(
                        source_directory=source_directory,
                        test_cases=executable_tests,
                        base_url=sut_url,
                        timeout_seconds=timeout_seconds,
                        preparation_failures=failures,
                    )
            else:
                outcome = self._execution.execute(
                    source_directory=source_directory,
                    test_cases=tests,
                    base_url="",
                    timeout_seconds=timeout_seconds,
                    preparation_failures=failures,
                )
            self._runtime_runs.complete(
                run, results=outcome.results, summary=outcome.summary,
                duration_ms=outcome.duration_ms,
            )
            return run
        except Exception as error:
            self._runtime_runs.fail(run, str(error))
            self._code_runs.fail(source_run, str(error), failed_stage="runtime_validation")
            raise

    @classmethod
    def _runtime_inputs(
        cls, result: dict,
    ) -> tuple[list[TestCase | RuntimeExecutionTarget], list[dict], set[str]]:
        plan_payload = result.get("runtime_execution_plan")
        if plan_payload is not None:
            plan = RuntimeExecutionPlan.model_validate(plan_payload)
            tests, failures = cls._from_runtime_plan(plan)
            return tests, failures, {item.test_case_id for item in plan.targets}
        optimization = result.get("quality_optimization")
        suite = (
            optimization.get("optimized_test_suite")
            if isinstance(optimization, dict)
            else None
        )
        if not isinstance(suite, list) or not suite:
            generation = result.get("test_generation")
            suite = (
                generation.get("generated_test_cases")
                if isinstance(generation, dict)
                else None
            )
        if not isinstance(suite, list) or not suite:
            raise RuntimeArtifactNotReadyError(
                "A runtime execution plan or completed generated unit suite is required"
            )
        tests = [TestCase.model_validate(item) for item in suite]
        return tests, [], {item.id for item in tests}

    @staticmethod
    def _from_runtime_plan(
        plan: RuntimeExecutionPlan,
    ) -> tuple[list[RuntimeExecutionTarget], list[dict]]:
        global_issues: dict[str, list] = {}
        for issue in plan.issues:
            global_issues.setdefault(issue.test_case_id, []).append(issue)
        executable, failures = [], []
        for target in plan.targets:
            issues = target.issues or global_issues.get(target.test_case_id, [])
            if (
                target.executable
                and target.classification in {"UNIT", "HTTP"}
                and not issues
            ):
                executable.append(target)
                continue
            reasons = [
                {"code": item.code, "message": item.message} for item in issues
            ] or [{
                "code": "not_executable_unit",
                "message": "Target is not an executable Stage 4 unit contract",
            }]
            failures.append({
                "test_case_id": target.test_case_id,
                "runtime_status": "NotExecutable",
                "expected_result": {"source": "Runtime Preparation", "issues": reasons},
                "actual_result": None,
                "assertion_failure": "; ".join(item["message"] for item in reasons),
                "logs": None,
                "execution_time_ms": 0.0,
            })
        return executable, failures

    @classmethod
    def _dependency_closure(
        cls,
        tests: list[TestCase | RuntimeExecutionTarget],
        requested: set[str],
    ) -> set[str]:
        """Include prerequisite creators when callers select dependent tests."""
        selected = set(requested)
        targets = {
            item.test_case_id: item for item in tests
            if isinstance(item, RuntimeExecutionTarget)
        }
        changed = True
        while changed:
            changed = False
            for case_id in list(selected):
                target = targets.get(case_id)
                if target is None:
                    continue
                dependency = target.traceability.get("depends_on", {})
                dependency_id = (
                    dependency.get("test_case_id")
                    if isinstance(dependency, dict) else None
                )
                if dependency_id in targets and dependency_id not in selected:
                    selected.add(dependency_id)
                    changed = True
        return selected

    def retry_pipeline(
        self, source_run_id: uuid.UUID, *, timeout_seconds: int = 120
    ) -> RuntimeValidationRun:
        source_run = self._code_runs.get_by_id(source_run_id)
        if (
            source_run is None
            or source_run.status != CodeUnderstandingStatus.FAILED
            or source_run.failed_stage != "runtime_validation"
        ):
            raise RuntimeArtifactNotReadyError(
                "Runtime Validation is not the failed pipeline stage"
            )
        previous = self._runtime_runs.get_latest_by_source_run_id(source_run_id)
        if previous is None or previous.status != "failed":
            raise RuntimeArtifactNotReadyError("Failed Runtime Validation run not found")
        self._code_runs.prepare_retry(source_run)
        retried = self.run(
            project_id=source_run.project_id,
            code_understanding_run_id=source_run.id,
            base_url=previous.base_url,
            test_case_ids=None,
            timeout_seconds=timeout_seconds,
        )
        self._code_runs.complete(source_run, dict(source_run.result or {}))
        return retried

    @staticmethod
    def _test_case_id(case: TestCase | RuntimeExecutionTarget) -> str:
        return case.id if isinstance(case, TestCase) else case.test_case_id

    def get_run(self, run_id: uuid.UUID) -> RuntimeValidationRun:
        run = self._runtime_runs.get_by_id(run_id)
        if run is None:
            raise RuntimeValidationRunNotFoundError("Runtime validation run not found")
        return run

    def get_report(self, run_id: uuid.UUID) -> RuntimeValidationReport:
        run = self.get_run(run_id)
        if run.summary is None:
            raise RuntimeArtifactNotReadyError("Runtime report is not available")
        results = [{
            "test_case_id": item.test_case_id,
            "runtime_status": item.runtime_status,
            "expected_result": item.expected_result,
            "actual_result": item.actual_result,
            "assertion_failure": item.assertion_failure,
            "logs": item.logs,
            "execution_time_ms": item.execution_time_ms,
        } for item in run.results]
        return RuntimeValidationReport(
            run_id=run.id,
            project_id=run.project_id,
            source_stage_run_id=run.source_stage_run_id,
            status=run.status,
            summary=run.summary,
            pass_rate=float(run.summary.get("pass_rate", 0)),
            duration_ms=float(run.duration_ms or 0),
            failed_tests=[item["test_case_id"] for item in results if item["runtime_status"] == "Failed"],
            skipped_tests=[item["test_case_id"] for item in results if item["runtime_status"] in {"Skipped", "NotExecutable"}],
            results=results,
        )


__all__ = [
    "RuntimeArtifactNotReadyError", "RuntimeProjectNotFoundError",
    "RuntimeSourceRunNotFoundError", "RuntimeValidationError",
    "RuntimeValidationRunNotFoundError", "RuntimeValidationService",
]
