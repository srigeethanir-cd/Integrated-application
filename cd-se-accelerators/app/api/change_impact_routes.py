import logging
import os
import json
from fastapi import APIRouter, HTTPException, status
from typing import Optional

from app.models.change_impact_models import (
    ChangeImpactRequest,
    ChangeImpactResponse,
    RunImpactTestsRequest,
)
from app.models.test_execution_models import TestExecutionReport
from app.services.change_impact.change_impact_service import ChangeImpactService
from app.services.test_execution.execution_service import TestExecutionService, find_run_dir
from app.db.repository import ProjectRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/change-impact", tags=["Change Impact Smart Test Selection"])

_change_impact_service = ChangeImpactService()
_execution_service = TestExecutionService()
_project_repo = ProjectRepository()


@router.post(
    "/analyze",
    response_model=ChangeImpactResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze Change Impact on Test Suites",
    description="Deterministic graph-based traversal identifying impacted components, test cases, and files.",
)
async def analyze_change_impact(request: ChangeImpactRequest) -> ChangeImpactResponse:
    """Analyze change impact using automatic project snapshot differences."""
    try:
        if not request.project_id:
            try:
                request.project_id = _project_repo.resolve_project_id(request.pipeline_run_id)
            except Exception:
                pass

        if not request.project_path:
            proj = None
            if request.project_id:
                proj = _project_repo.get_project(request.project_id)
            if proj and os.path.exists(proj.project_path):
                request.project_path = proj.project_path
            else:
                # Try locating by pipeline run directory
                try:
                    project_path, _ = find_run_dir(request.pipeline_run_id)
                    request.project_path = project_path
                except Exception:
                    pass

        if not request.project_path or not os.path.exists(request.project_path):
            raise FileNotFoundError(f"Project directory path '{request.project_path}' could not be resolved or does not exist on disk.")

        return _change_impact_service.analyze_impact(request)
    except FileNotFoundError as exc:
        logger.warning("Project path or file not found during analysis: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        )
    except Exception as exc:
        logger.exception("Change impact analysis failed unexpectedly")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Change impact analysis failed: {exc}",
        )


@router.post(
    "/run-tests",
    response_model=TestExecutionReport,
    status_code=status.HTTP_200_OK,
    summary="Run Recommended Impacted Tests",
    description="Run Jest on recommended test files for the given pipeline run.",
)
async def run_impact_tests(request: RunImpactTestsRequest) -> TestExecutionReport:
    """Execute recommended Jest tests based on change impact analysis."""
    try:
        pipeline_run_id = request.pipeline_run_id
        
        # Resolve project paths
        project_path, run_dir = find_run_dir(pipeline_run_id)
        
        # Load or compute change impact analysis report
        analysis_result = None
        
        if request.changed_files:
            # Re-run analysis on the fly
            analysis_req = ChangeImpactRequest(
                project_path=project_path,
                changed_files=request.changed_files,
                pipeline_run_id=pipeline_run_id
            )
            analysis_result = _change_impact_service.analyze_impact(analysis_req)
        else:
            # Load stored analysis from file
            persistent_analysis_file = os.path.join(
                _change_impact_service._get_persistent_run_dir(pipeline_run_id),
                "change_impact_analysis.json"
            )
            if os.path.exists(persistent_analysis_file):
                try:
                    with open(persistent_analysis_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    analysis_result = ChangeImpactResponse.model_validate(data)
                except Exception as exc:
                    logger.warning("Failed loading stored analysis: %s", exc)
            
            # If still not found, try to run a default analysis on the components to get list
            if not analysis_result:
                # No analysis exists yet; default to running all tests
                logger.info("No stored change impact report found. Running all test suites.")
                return _execution_service.execute_pipeline_tests(pipeline_run_id)

        # Retrieve unique test files recommended by analysis
        recommended_files = list({item.test_file for item in analysis_result.recommended_tests})
        logger.info("Executing recommended test files: %s", recommended_files)

        # Run tests on recommended files
        execution_report = _execution_service.execute_pipeline_tests(
            pipeline_run_id=pipeline_run_id,
            run_only_files=recommended_files
        )

        # Save test execution report and results to Database using project repository
        try:
            proj_id = _project_repo.resolve_project_id(pipeline_run_id)
            _project_repo.save_test_execution_and_results(proj_id, pipeline_run_id, execution_report)
        except Exception as db_exc:
            logger.warning("Could not persist test execution results to Database: %s", db_exc)

        return execution_report
        
    except FileNotFoundError as exc:
        logger.warning("Pipeline run or file not found during test execution: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        )
    except Exception as exc:
        logger.exception("Executing recommended tests failed unexpectedly")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Executing recommended tests failed: {exc}",
        )
