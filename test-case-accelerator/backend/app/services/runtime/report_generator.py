from __future__ import annotations

from typing import Any


class ReportGenerator:
    @staticmethod
    def summary(results: list[dict[str, Any]]) -> dict[str, Any]:
        counts = {"passed": 0, "failed": 0, "skipped": 0, "not_executable": 0}
        mapping = {
            "Passed": "passed", "Failed": "failed", "Skipped": "skipped",
            "NotExecutable": "not_executable",
        }
        for result in results:
            counts[mapping[result["runtime_status"]]] += 1
        total = len(results)
        counts["total"] = total
        executed = counts["passed"] + counts["failed"]
        counts["executed"] = executed
        counts["pass_rate"] = (
            round(counts["passed"] / executed * 100, 2) if executed else 0.0
        )
        preparation_failures = sum(
            isinstance(result.get("expected_result"), dict)
            and result["expected_result"].get("source") == "Runtime Preparation"
            for result in results
        )
        if preparation_failures:
            counts["runtime_preparation_failures"] = preparation_failures
        return counts
