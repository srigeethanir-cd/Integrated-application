"""
API routes for Test Case Storage & Retrieval.

Provides endpoints to retrieve persisted test case plans and pipeline run
summaries from the stable ``generated_tests/runs/`` directory.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, status

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/test_cases", tags=["Test Case Storage"])

# Stable persistent runs directory (same as pipeline orchestrator)
PERSISTENT_RUNS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "generated_tests",
    "runs",
)


def _load_json_file(file_path: str) -> Optional[Dict[str, Any]]:
    """Safely load a JSON file and return its contents."""
    if not os.path.exists(file_path):
        return None
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        logger.warning("Failed to load JSON from %s: %s", file_path, exc)
        return None


def _get_sorted_run_dirs() -> List[str]:
    """Return run directory names sorted by modification time (newest first)."""
    if not os.path.isdir(PERSISTENT_RUNS_DIR):
        return []
    run_dirs = []
    for entry in os.listdir(PERSISTENT_RUNS_DIR):
        full_path = os.path.join(PERSISTENT_RUNS_DIR, entry)
        if os.path.isdir(full_path):
            run_dirs.append((entry, os.path.getmtime(full_path)))
    # Sort by modification time descending (newest first)
    run_dirs.sort(key=lambda x: x[1], reverse=True)
    return [name for name, _ in run_dirs]


@router.get(
    "/latest",
    status_code=status.HTTP_200_OK,
    summary="Get Latest Test Case Plan",
    description="Returns the most recently generated test case plan from persistent storage.",
)
async def get_latest_test_cases() -> Dict[str, Any]:
    """Retrieve the most recent test case plan."""
    sorted_runs = _get_sorted_run_dirs()

    for run_id in sorted_runs:
        plan_path = os.path.join(PERSISTENT_RUNS_DIR, run_id, "test_case_plan.json")
        plan = _load_json_file(plan_path)
        if plan:
            # Also load pipeline result for metadata
            result_path = os.path.join(PERSISTENT_RUNS_DIR, run_id, "pipeline_result.json")
            pipeline_result = _load_json_file(result_path)

            # Load execution report if available
            exec_path = os.path.join(PERSISTENT_RUNS_DIR, run_id, "execution_report.json")
            execution_report = _load_json_file(exec_path)

            # Load validation report if available
            val_path = os.path.join(PERSISTENT_RUNS_DIR, run_id, "validation_report.json")
            validation_report = _load_json_file(val_path)

            # Load test report if available
            test_report_path = os.path.join(PERSISTENT_RUNS_DIR, run_id, "test_report.json")
            if not os.path.exists(test_report_path):
                test_report_path = os.path.join(PERSISTENT_RUNS_DIR, run_id, "reports", "test_report.json")
            test_report = _load_json_file(test_report_path)

            # Load test writer output if available
            writer_path = os.path.join(PERSISTENT_RUNS_DIR, run_id, "test_writer_output.json")
            test_writer_output = _load_json_file(writer_path)

            return {
                "pipeline_run_id": run_id,
                "test_case_plan": plan,
                "pipeline_result": pipeline_result,
                "execution_report": execution_report,
                "validation_report": validation_report,
                "test_report": test_report,
                "generated_test_files": test_writer_output,
            }

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="No stored test case plans found. Run the pipeline first.",
    )


@router.get(
    "/runs",
    status_code=status.HTTP_200_OK,
    summary="List All Stored Pipeline Runs",
    description="Returns metadata for all stored pipeline runs with test case plans.",
)
async def list_stored_runs() -> Dict[str, Any]:
    """List all stored pipeline runs."""
    sorted_runs = _get_sorted_run_dirs()
    runs = []

    for run_id in sorted_runs:
        run_dir = os.path.join(PERSISTENT_RUNS_DIR, run_id)
        result = _load_json_file(os.path.join(run_dir, "pipeline_result.json"))
        has_test_cases = os.path.exists(os.path.join(run_dir, "test_case_plan.json"))
        has_test_files = os.path.exists(os.path.join(run_dir, "test_writer_output.json"))
        has_execution = os.path.exists(os.path.join(run_dir, "execution_report.json"))

        runs.append({
            "pipeline_run_id": run_id,
            "status": result.get("status", "unknown") if result else "unknown",
            "framework": result.get("framework") if result else None,
            "completed_at": result.get("completed_at") if result else None,
            "completed_stages": result.get("completed_stages", []) if result else [],
            "total_execution_time_ms": result.get("total_execution_time_ms", 0) if result else 0,
            "has_test_cases": has_test_cases,
            "has_test_files": has_test_files,
            "has_execution_report": has_execution,
        })

    return {"total_runs": len(runs), "runs": runs}


@router.get(
    "/{pipeline_run_id}",
    status_code=status.HTTP_200_OK,
    summary="Get Test Case Plan by Run ID",
    description="Returns the test case plan for a specific pipeline run.",
)
async def get_test_cases_by_run_id(pipeline_run_id: str) -> Dict[str, Any]:
    """Retrieve test case plan for a specific pipeline run."""
    run_dir = os.path.join(PERSISTENT_RUNS_DIR, pipeline_run_id)

    if not os.path.isdir(run_dir):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pipeline run '{pipeline_run_id}' not found.",
        )

    plan = _load_json_file(os.path.join(run_dir, "test_case_plan.json"))
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No test case plan found for run '{pipeline_run_id}'.",
        )

    result = _load_json_file(os.path.join(run_dir, "pipeline_result.json"))
    execution_report = _load_json_file(os.path.join(run_dir, "execution_report.json"))
    validation_report = _load_json_file(os.path.join(run_dir, "validation_report.json"))
    test_writer_output = _load_json_file(os.path.join(run_dir, "test_writer_output.json"))
    test_report_path = os.path.join(run_dir, "test_report.json")
    if not os.path.exists(test_report_path):
        test_report_path = os.path.join(run_dir, "reports", "test_report.json")
    test_report = _load_json_file(test_report_path)

    return {
        "pipeline_run_id": pipeline_run_id,
        "test_case_plan": plan,
        "pipeline_result": result,
        "execution_report": execution_report,
        "validation_report": validation_report,
        "test_report": test_report,
        "generated_test_files": test_writer_output,
    }
