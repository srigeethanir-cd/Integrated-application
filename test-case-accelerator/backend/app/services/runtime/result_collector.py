from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from app.services.runtime.pytest_runner import PytestRunResult
from app.services.runtime.test_file_builder import ExecutableTest


class ResultCollector:
    def collect(
        self, run: PytestRunResult, executable: list[ExecutableTest],
        result_directory: Path,
    ) -> list[dict[str, Any]]:
        by_name = {item.function_name: item for item in executable}
        collected: dict[str, dict[str, Any]] = {}
        if run.junit_path.is_file():
            root = ET.parse(run.junit_path).getroot()
            for node in root.iter("testcase"):
                pytest_name = node.attrib.get("name", "")
                specification = by_name.get(pytest_name) or by_name.get(
                    pytest_name.split("[", 1)[0]
                )
                if specification is None:
                    continue
                failure = node.find("failure")
                if failure is None:
                    failure = node.find("error")
                skipped = node.find("skipped")
                status = "Skipped" if skipped is not None else "Failed" if failure is not None else "Passed"
                sidecar = self._sidecar(result_directory, specification.result_key)
                failure_text = (
                    (failure.text or failure.attrib.get("message")) if failure is not None
                    else skipped.attrib.get("message") if skipped is not None else None
                )
                category = None
                action = None
                if status == "Failed":
                    category = "Developer Code Issue"
                    action = "Review the target function implementation to ensure it satisfies expected return types, status codes, and exception contracts."
                elif status == "NotExecutable":
                    category = "Test Generation Issue"
                    action = "Check test specification, module import path, and function signature."

                collected[specification.case_id] = {
                    "test_case_id": specification.case_id,
                    "runtime_status": status,
                    "expected_result": specification.expected_result,
                    "actual_result": sidecar.get("actual_result"),
                    "assertion_failure": failure_text,
                    "failure_category": category,
                    "developer_action": action,
                    "suggested_fix": action,
                    "logs": self._logs(run),
                    "execution_time_ms": float(node.attrib.get("time", 0)) * 1000,
                }
        for specification in executable:
            if specification.case_id not in collected:
                failure_text = (
                    "Runtime validation timed out"
                    if run.timed_out else "Pytest did not produce a result for this test"
                )
                collected[specification.case_id] = {
                    "test_case_id": specification.case_id,
                    "runtime_status": "Skipped" if run.timed_out else "Failed",
                    "expected_result": specification.expected_result,
                    "actual_result": self._sidecar(result_directory, specification.result_key).get("actual_result"),
                    "assertion_failure": failure_text,
                    "failure_category": "Test Infrastructure Issue" if run.timed_out else "Developer Code Issue",
                    "developer_action": "Verify execution timeout and system resources." if run.timed_out else "Review target function implementation for runtime failure.",
                    "suggested_fix": "Verify execution timeout and system resources." if run.timed_out else "Review target function implementation for runtime failure.",
                    "logs": self._logs(run),
                    "execution_time_ms": 0.0,
                }
        return list(collected.values())

    @staticmethod
    def _sidecar(directory: Path, case_id: str) -> dict[str, Any]:
        path = directory / f"{case_id}.json"
        try:
            return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
        except (OSError, json.JSONDecodeError):
            return {}

    @staticmethod
    def _logs(run: PytestRunResult) -> str | None:
        value = "\n".join(item for item in (run.stdout, run.stderr) if item)
        return value[-100_000:] or None
