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

        # Issue Category Breakdown:
        # Developer Code Issues: Valid executable tests that failed assertion/contract checks
        # Test Infrastructure Issues: Execution timeouts, environment setup failures
        # Test Generation Issues: Unresolvable targets / NotExecutable tests
        counts["developer_code_issues"] = sum(
            1 for r in results if r["runtime_status"] == "Failed" and r.get("failure_category") != "Test Infrastructure Issue"
        )
        counts["test_infrastructure_issues"] = sum(
            1 for r in results if r.get("failure_category") == "Test Infrastructure Issue"
        )
        counts["test_generation_issues"] = counts["not_executable"] + sum(
            1 for r in results if r.get("failure_category") == "Test Generation Issue"
        )

        # Calculate overall test suite quality score based on executability and pass performance
        executability_ratio = executed / total if total else 0.0
        pass_ratio = (counts["passed"] / executed) if executed else 0.0
        quality_percent = round((executability_ratio * 0.4 + pass_ratio * 0.6) * 100, 1)
        counts["quality_percent"] = quality_percent
        counts["test_quality_score"] = quality_percent
        return counts
