"""
API routes for E2E Validation & QA Engine – Module 9.

Triggers E2E compilation checks, test execution checks, quality audit scans,
and code coverage mappings.
"""

import logging
import os
from fastapi import APIRouter, HTTPException, status

from app.models.validation_models import ValidationRequest, ValidationReport
from app.services.validation.validation_service import ValidationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/validation", tags=["Validation"])

_service = ValidationService()


@router.post(
    "/run",
    response_model=ValidationReport,
    status_code=status.HTTP_200_OK,
    summary="Execute Test validation and QA auditing",
    description="Run E2E compilation syntax validations, check code quality scores, "
                "verify manifest mappings, and configure coverage summary files.",
)
async def run_validation(
    request: ValidationRequest,
) -> ValidationReport:
    """Run E2E validation audits on generated frontend test suites."""
    try:
        project_path = request.project_path
        framework = request.framework or "React"

        if not project_path and request.generated_test_files:
            if request.generated_test_files.manifest_path:
                project_path = os.path.dirname(os.path.abspath(request.generated_test_files.manifest_path))

        if not project_path:
            raise ValueError("ValidationRequest requires either 'project_path' or 'generated_test_files'.")

        res = _service.run_validation(project_path, framework)
        if not res.validation_passed:
            logger.warning("E2E validation checks failed: %s", res.errors)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"E2E Validation check failed: {res.errors}"
            )
        return res
    except FileNotFoundError as exc:
        logger.warning("Manifest not found error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        )
    except ValueError as exc:
        logger.warning("Validation payload constraint error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        )
    except HTTPException as exc:
        raise exc
    except Exception as exc:
        logger.exception("E2E validation execution failed unexpectedly")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"E2E Validation run failed: {exc}",
        )
