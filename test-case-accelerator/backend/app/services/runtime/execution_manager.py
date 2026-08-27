from __future__ import annotations

import tempfile
import time
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.schemas.runtime_preparation import RuntimeExecutionTarget
from app.schemas.test_case import TestCase
from app.services.runtime.pytest_runner import PytestRunner
from app.services.runtime.report_generator import ReportGenerator
from app.services.runtime.result_collector import ResultCollector
from app.services.runtime.test_file_builder import TestFileBuilder
from app.services.runtime.dependency_preparer import DependencyPreparer


@dataclass(frozen=True)
class ExecutionOutcome:
    results: list[dict[str, Any]]
    summary: dict[str, Any]
    duration_ms: float


class ExecutionManager:
    def __init__(
        self,
        builder: TestFileBuilder,
        runner: PytestRunner,
        collector: ResultCollector,
        reporter: ReportGenerator,
        dependency_preparer: DependencyPreparer | None = None,
    ) -> None:
        self._builder = builder
        self._runner = runner
        self._collector = collector
        self._reporter = reporter
        self._dependency_preparer = dependency_preparer or DependencyPreparer()

    def execute(
        self, *, source_directory: Path,
        test_cases: list[TestCase | RuntimeExecutionTarget],
        base_url: str, timeout_seconds: int,
        preparation_failures: list[dict[str, Any]] | None = None,
    ) -> ExecutionOutcome:
        if not source_directory.is_dir():
            raise FileNotFoundError("Project source directory does not exist")
        started = time.perf_counter()
        with tempfile.TemporaryDirectory(prefix="testforge-runtime-") as temporary:
            workspace = Path(temporary)
            runtime_source = workspace / "source"
            shutil.copytree(source_directory, runtime_source)
            dependency_result = self._dependency_preparer.prepare(
                runtime_source,
                workspace=workspace,
                timeout_seconds=timeout_seconds,
            )
            if not dependency_result.success:
                results = list(preparation_failures or [])
                results.extend(
                    self._dependency_failure(case, dependency_result.error)
                    for case in test_cases
                )
                duration_ms = (time.perf_counter() - started) * 1000
                return ExecutionOutcome(
                    results=results,
                    summary=self._reporter.summary(results),
                    duration_ms=duration_ms,
                )
            build = self._builder.build(
                test_cases, workspace=workspace, base_url=base_url
            )
            results = list(preparation_failures or [])
            results.extend(build.not_executable)
            if build.test_file is not None:
                pytest_result = self._runner.run(
                    build.test_file,
                    timeout_seconds=timeout_seconds,
                    python_path=runtime_source,
                    dependency_path=dependency_result.dependency_path,
                )
                results.extend(self._collector.collect(
                    pytest_result, build.executable, build.result_directory
                ))
            duration_ms = (time.perf_counter() - started) * 1000
            summary = self._reporter.summary(results)
            if build.test_file is not None and pytest_result.coverage_percent is not None:
                summary["coverage_percent"] = pytest_result.coverage_percent
            return ExecutionOutcome(
                results=results,
                summary=summary,
                duration_ms=duration_ms,
            )

    @staticmethod
    def _dependency_failure(
        case: TestCase | RuntimeExecutionTarget, error: str | None
    ) -> dict[str, Any]:
        case_id = case.id if isinstance(case, TestCase) else case.test_case_id
        return {
            "test_case_id": case_id,
            "runtime_status": "NotExecutable",
            "expected_result": {
                "kind": "dependency_preparation",
                "source": "Runtime Preparation",
            },
            "actual_result": None,
            "assertion_failure": error or "Dependency preparation failed",
            "logs": error,
            "execution_time_ms": 0.0,
        }
