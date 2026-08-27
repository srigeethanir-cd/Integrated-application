"""Stage 3 code-understanding API."""

import uuid
from collections.abc import Callable
from typing import TypeVar

from fastapi import APIRouter, HTTPException, status
from openai import OpenAIError
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.agents.code_understanding.client import StructuredOutputClientError
from app.agents.test_generation.test_generation_agent import TestGenerationError
from app.agents.semantic_verification.agent import TestVerificationError
from app.dependencies.code_understanding import CodeUnderstandingServiceDependency
from app.dependencies.runtime_validation import RuntimeValidationServiceDependency
from app.api.v1.endpoints.security_scans import _response as security_scan_response
from app.schemas.code_understanding import (
    CodeUnderstandingRequest,
    CodeUnderstandingResponse,
    PipelineStateResponse,
    TestGenerationRequest,
    TestGenerationResponse,
    TestVerificationRequest,
    TestVerificationResponse,
)
from app.schemas.dependency import DependencyRunDetail
from app.schemas.file_metadata import FileMetadata
from app.schemas.runtime_preparation import RuntimeExecutionPlan
from app.schemas.test_quality import (
    QualityEvaluation,
    QualityEvaluationRequest,
    QualityLoopResult,
    QualityOptimizationRequest,
)
from app.services.code_understanding.code_understanding_service import (
    CodeUnderstandingRunNotFoundError,
    CodeUnderstandingRunNotReadyError,
    DependencyRunNotFoundError,
    DependencyRunNotReadyError,
    InvalidSourcePathError,
    ProjectNotFoundError,
)
from app.services.code_understanding.public_artifact import public_pipeline_result

router = APIRouter(tags=["code-understanding"])
ResultT = TypeVar("ResultT")


@router.post(
    "/projects/{project_id}/understand",
    response_model=CodeUnderstandingResponse,
    status_code=status.HTTP_201_CREATED,
)
def understand_project(
    project_id: uuid.UUID,
    request: CodeUnderstandingRequest,
    service: CodeUnderstandingServiceDependency,
) -> CodeUnderstandingResponse:
    run = _execute(lambda: service.understand(project_id, request.dependency_run_id))
    return _run_response(run)


@router.post(
    "/projects/{project_id}/pipeline",
    response_model=CodeUnderstandingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Run the backward-compatible Stage 3-5 pipeline",
)
def run_pipeline(
    project_id: uuid.UUID,
    request: CodeUnderstandingRequest,
    service: CodeUnderstandingServiceDependency,
) -> CodeUnderstandingResponse:
    run = _execute(lambda: service.run(project_id, request.dependency_run_id))
    return _run_response(run)


@router.post(
    "/pipeline/{run_id}/retry",
    response_model=CodeUnderstandingResponse,
    summary="Resume a failed pipeline from its first failed stage",
)
def retry_pipeline(
    run_id: uuid.UUID,
    service: CodeUnderstandingServiceDependency,
    runtime_service: RuntimeValidationServiceDependency,
) -> CodeUnderstandingResponse:
    run = service.get_run(run_id)
    if run is not None and run.failed_stage == "runtime_validation":
        _execute(lambda: runtime_service.retry_pipeline(run_id))
        run = service.get_run(run_id)
        assert run is not None
        return _run_response(run)
    return _run_response(_execute(lambda: service.retry(run_id)))


@router.post(
    "/projects/{project_id}/generate-test-cases",
    response_model=TestGenerationResponse,
    summary="Generate test cases from a completed Stage 3 run",
)
def generate_test_cases(
    project_id: uuid.UUID,
    request: TestGenerationRequest,
    service: CodeUnderstandingServiceDependency,
) -> TestGenerationResponse:
    result = _execute(
        lambda: service.generate_test_cases(
            project_id, request.code_understanding_run_id
        )
    )
    return TestGenerationResponse.model_validate(result)


@router.post(
    "/projects/{project_id}/verify-test-cases",
    response_model=TestVerificationResponse,
    summary="Verify test cases against a completed Stage 3 run",
)
def verify_test_cases(
    project_id: uuid.UUID,
    request: TestVerificationRequest,
    service: CodeUnderstandingServiceDependency,
) -> TestVerificationResponse:
    result = _execute(
        lambda: service.verify_test_cases(
            project_id,
            request.code_understanding_run_id,
            request.test_cases,
        )
    )
    return TestVerificationResponse.model_validate(result)


@router.post(
    "/projects/{project_id}/evaluate-test-quality",
    response_model=QualityEvaluation,
    summary="Evaluate Stage 5 test-suite quality",
)
def evaluate_test_quality(
    project_id: uuid.UUID,
    request: QualityEvaluationRequest,
    service: CodeUnderstandingServiceDependency,
) -> QualityEvaluation:
    return _execute(
        lambda: service.evaluate_test_quality(
            project_id,
            request.code_understanding_run_id,
            request.test_cases,
            request.verification.model_dump(mode="json"),
        )
    )


@router.post(
    "/projects/{project_id}/optimize-test-quality",
    response_model=QualityLoopResult,
    summary="Optimize a Stage 5 test suite through the Stage 4-6 feedback loop",
)
def optimize_test_quality(
    project_id: uuid.UUID,
    request: QualityOptimizationRequest,
    service: CodeUnderstandingServiceDependency,
) -> QualityLoopResult:
    return _execute(
        lambda: service.optimize_test_quality(
            project_id,
            request.code_understanding_run_id,
            request.test_cases,
            request.verification.model_dump(mode="json"),
        )
    )





def _safe_model_parse(model_cls: type[ResultT], data: object) -> ResultT | None:
    if data is None:
        return None
    try:
        if isinstance(data, model_cls):
            return data
        return model_cls.model_validate(data)
    except Exception:
        return None


@router.get(
    "/projects/{project_id}/pipeline-state",
    response_model=PipelineStateResponse,
)
def get_latest_pipeline_state(
    project_id: uuid.UUID,
    service: CodeUnderstandingServiceDependency,
) -> PipelineStateResponse:
    state = _execute(lambda: service.get_latest_pipeline_state(project_id))
    dependency_run = state["dependency_run"]
    understanding_run = state["understanding_run"]
    retry_metadata = _retry_metadata(understanding_run)
    return PipelineStateResponse(
        project_id=project_id,
        security_scan=(
            security_scan_response(security_run)
            if (security_run := state.get("security_scan_run"))
            else None
        ),
        dependency=(
            DependencyRunDetail(
                run_id=dependency_run.id,
                project_id=dependency_run.project_id,
                project_path=dependency_run.project_path,
                status=dependency_run.status,
                files=[
                    FileMetadata.model_validate(file, from_attributes=True)
                    for file in (dependency_run.files or [])
                ],
            )
            if dependency_run is not None
            else None
        ),
        understanding=(
            _run_response(
                understanding_run,
                include_pipeline_artifacts=state.get(
                    "artifacts_publishable", True
                ),
            )
            if understanding_run is not None
            else None
        ),
        generation=_safe_model_parse(
            TestGenerationResponse, state.get("test_generation")
        ),
        verification=_safe_model_parse(
            TestVerificationResponse, state.get("test_verification")
        ),
        quality=_safe_model_parse(
            QualityLoopResult, state.get("quality_optimization")
        ),
        runtime_preparation=_safe_model_parse(
            RuntimeExecutionPlan, state.get("runtime_execution_plan")
        ),
        failed_stage=retry_metadata["failed_stage"],
        failure_reason=retry_metadata["failure_reason"],
        retry_count=retry_metadata["retry_count"],
        last_successful_stage=retry_metadata["last_successful_stage"],
        resumed_stage=(
            retry_metadata["failed_stage"]
            if retry_metadata["retry_count"]
            else None
        ),
    )


@router.get(
    "/projects/{project_id}/code-understanding-runs/latest",
    response_model=CodeUnderstandingResponse,
)
def get_latest_code_understanding_run(
    project_id: uuid.UUID,
    service: CodeUnderstandingServiceDependency,
) -> CodeUnderstandingResponse:
    run = _execute(lambda: service.get_latest_run(project_id))
    if run is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "Code-understanding run not found"
        )
    return _run_response(run)


@router.get(
    "/projects/{project_id}/generated-test-cases/latest",
    response_model=TestGenerationResponse,
)
def get_latest_generated_test_cases(
    project_id: uuid.UUID,
    service: CodeUnderstandingServiceDependency,
) -> TestGenerationResponse:
    state = _execute(lambda: service.get_latest_pipeline_state(project_id))
    generation = state["test_generation"]
    if generation is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Generated test cases not found")
    return TestGenerationResponse.model_validate(generation)


@router.get(
    "/projects/{project_id}/verification-results/latest",
    response_model=TestVerificationResponse,
)
def get_latest_verification_results(
    project_id: uuid.UUID,
    service: CodeUnderstandingServiceDependency,
) -> TestVerificationResponse:
    state = _execute(lambda: service.get_latest_pipeline_state(project_id))
    verification = state["test_verification"]
    if verification is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Verification results not found")
    return TestVerificationResponse.model_validate(verification)


def _run_response(
    run, *, include_pipeline_artifacts: bool = True
) -> CodeUnderstandingResponse:
    metadata = _retry_metadata(run)
    result = public_pipeline_result(run.result)
    if isinstance(result, dict):
        if not include_pipeline_artifacts or run.status != "completed":
            for key in (
                "test_generation", "test_verification",
                "quality_evaluation", "quality_optimization",
                "runtime_execution_plan",
            ):
                result.pop(key, None)
    return CodeUnderstandingResponse(
        run_id=run.id,
        status=run.status,
        result=result,
        **metadata,
    )


def _retry_metadata(run) -> dict:
    if run is None:
        return {
            "failed_stage": None,
            "failure_reason": None,
            "retry_count": 0,
            "last_successful_stage": None,
        }
    failed_stage = getattr(run, "failed_stage", None)
    failure_reason = getattr(run, "failure_reason", None)
    retry_count = getattr(run, "retry_count", 0)
    last_successful_stage = getattr(run, "last_successful_stage", None)
    return {
        "failed_stage": failed_stage if isinstance(failed_stage, str) else None,
        "failure_reason": (
            failure_reason if isinstance(failure_reason, str) else None
        ),
        "retry_count": retry_count if isinstance(retry_count, int) else 0,
        "last_successful_stage": (
            last_successful_stage
            if isinstance(last_successful_stage, str)
            else None
        ),
    }


def _execute(operation: Callable[[], ResultT]) -> ResultT:
    try:
        return operation()
    except (
        ProjectNotFoundError,
        DependencyRunNotFoundError,
        CodeUnderstandingRunNotFoundError,
    ) as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error
    except (
        DependencyRunNotReadyError,
        InvalidSourcePathError,
        CodeUnderstandingRunNotReadyError,
    ) as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error
    except SQLAlchemyError as error:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "Database operation failed",
        ) from error
    except (OpenAIError, StructuredOutputClientError, ValidationError) as error:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            "Code-understanding provider failed",
        ) from error
    except TestGenerationError as error:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            "Test-generation provider failed",
        ) from error
    except TestVerificationError as error:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            "Test-verification provider failed",
        ) from error
    except OSError as error:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Code understanding failed",
        ) from error
