"""
Test Execution Service – Module 10.

Orchestrates locating run directories, executing Jest tests on generated test suites,
collecting reports/coverage summaries, and persisting report outputs.
"""

import json
import logging
import os
import shutil
from typing import Any, Dict, List, Tuple
from pathlib import Path

from app.models.test_case_models import TestCase, TestCasePlanResponse
from app.models.test_execution_models import TestExecutionReport
from app.services.test_execution.registry import (
    TestExecutionRegistry,
    build_default_test_execution_registry,
)

logger = logging.getLogger(__name__)


def find_run_dir(pipeline_run_id: str) -> Tuple[str, str]:
    """Find source project path and runs subdirectory by pipeline run ID."""
    patterns = [
        "app/uploads/*/source/runs/*",
        "app/uploads/*/runs/*",
        "uploads/*/source/runs/*",
        "uploads/*/runs/*",
        "scratch/test_workspace/*/source/runs/*",
        "scratch/test_workspace/*/runs/*",
        "scratch/test_workspace/runs/*",
        "runs/*",
        "uploads/runs/*",
        "temp/runs/*"
    ]
    # Check current directory and application root directory
    base_dirs = [Path("."), Path(__file__).resolve().parent.parent.parent]
    
    for base in base_dirs:
        for pattern in patterns:
            try:
                for p in base.glob(pattern):
                    if p.name == pipeline_run_id:
                        proj_path = p.parent.parent
                        # If project has a source subfolder (uploaded project), use that as the execution root
                        if (proj_path / "source").exists():
                            return str(proj_path / "source"), str(p)
                        return str(proj_path), str(p)
            except Exception:
                pass
                
    # Direct folder lookup fallback
    # If not found via globbing, search by directly looking under temp or scratch
    fallback_dirs = ["scratch/test_workspace", "uploads", "temp"]
    for fd in fallback_dirs:
        if os.path.exists(fd):
            for item in os.listdir(fd):
                sub_path = os.path.join(fd, item)
                if os.path.isdir(sub_path):
                    runs_path = os.path.join(sub_path, "runs", pipeline_run_id)
                    if os.path.exists(runs_path):
                        source_path = os.path.join(sub_path, "source")
                        if os.path.exists(source_path):
                            return source_path, runs_path
                        return sub_path, runs_path

    raise FileNotFoundError(f"Pipeline run ID '{pipeline_run_id}' not found.")


class TestExecutionService:
    """Orchestrates test executions for generated files using registered Jest executors."""

    def __init__(self, registry: TestExecutionRegistry | None = None) -> None:
        self._registry = registry or build_default_test_execution_registry()
        logger.info(
            "TestExecutionService initialised with executors: %s",
            ", ".join(e for e in self._registry._executors.keys())
        )

    def execute_pipeline_tests(self, pipeline_run_id: str) -> TestExecutionReport:
        """Locate test files for pipeline_run_id, run Jest, and persist results."""
        logger.info("Starting test execution workflow for run: %s", pipeline_run_id)

        # 1. Locate project path and run directory
        project_path, run_dir = find_run_dir(pipeline_run_id)
        logger.info("Found project path: %s and run dir: %s", project_path, run_dir)

        # 2. Read test_manifest.json (with multi-path fallback)
        persistent_runs_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "generated_tests",
            "runs",
        )
        manifest_candidates = [
            os.path.join(run_dir, "test_manifest.json"),
            os.path.join(os.path.dirname(run_dir), "test_manifest.json"),
            os.path.join(os.path.dirname(os.path.dirname(run_dir)), "test_manifest.json"),
            os.path.join(project_path, "test_manifest.json"),
            os.path.join(os.path.dirname(project_path), "test_manifest.json"),
            os.path.join(project_path, "project-1", "generated_test_files", "test_manifest.json"),
            os.path.join(persistent_runs_dir, pipeline_run_id, "test_manifest.json"),
        ]

        manifest_path = None
        for cand in manifest_candidates:
            if os.path.exists(cand):
                manifest_path = cand
                break

        if not manifest_path:
            raise FileNotFoundError(f"test_manifest.json not found in run directory or fallbacks: {run_dir}")

        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        framework = manifest.get("framework", "React")

        # 3. Retrieve TestCase models from saved test_case_plan.json
        test_cases: List[TestCase] = []
        plan_candidates = [
            os.path.join(run_dir, "test_case_plan.json"),
            os.path.join(os.path.dirname(run_dir), "test_case_plan.json"),
            os.path.join(os.path.dirname(os.path.dirname(run_dir)), "test_case_plan.json"),
            os.path.join(project_path, "test_case_plan.json"),
            os.path.join(os.path.dirname(project_path), "test_case_plan.json"),
            os.path.join(project_path, "project-1", "generated_testcases", "test_cases.json"),
            os.path.join(persistent_runs_dir, pipeline_run_id, "test_case_plan.json"),
        ]
        plan_path = None
        for cand in plan_candidates:
            if os.path.exists(cand):
                plan_path = cand
                break

        if plan_path:
            try:
                with open(plan_path, "r", encoding="utf-8") as f:
                    plan_data = json.load(f)
                
                # Check for nested structure
                tcs_data = plan_data.get("test_cases", [])
                for tc_dict in tcs_data:
                    test_cases.append(TestCase.model_validate(tc_dict))
            except Exception as exc:
                logger.error("Failed to load test_case_plan.json for mapping: %s", exc)

        # 4. Resolve file paths listed in the manifest
        sub_folder = "react" if framework.lower() == "react" else "angular"
        tests_dir = os.path.join(project_path, "tests", sub_folder)
        
        test_files = []
        for file_info in manifest.get("generated_files", []):
            file_name = file_info.get("file", "")
            file_path = os.path.join(tests_dir, file_name)
            
            # Verify file exists on disk
            if os.path.exists(file_path):
                test_files.append(file_path)
            else:
                logger.warning("Manifest file %s not found on disk at %s", file_name, file_path)

        # 5. Execute using framework executor
        executor = self._registry.get_executor(framework)
        if not executor:
            raise ValueError(f"No test executor registered for framework: {framework}")

        report = executor.run_tests(
            project_path=project_path,
            pipeline_run_id=pipeline_run_id,
            test_files=test_files,
            test_cases=test_cases,
            manifest=manifest
        )

        # 6. Save report outputs persistently
        report_path = os.path.join(run_dir, "execution_report.json")
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report.model_dump(), f, indent=2)

        # If coverage directory was generated, copy to run directory
        temp_coverage_dir = os.path.join(project_path, f"coverage-{pipeline_run_id}")
        run_coverage_dir = os.path.join(run_dir, "coverage")
        if os.path.exists(temp_coverage_dir):
            try:
                if os.path.exists(run_coverage_dir):
                    shutil.rmtree(run_coverage_dir, ignore_errors=True)
                shutil.move(temp_coverage_dir, run_coverage_dir)
            except Exception as exc:
                logger.warning("Failed to move coverage summary output: %s", exc)

        logger.info("Successfully completed test execution report for run: %s", pipeline_run_id)
        return report
