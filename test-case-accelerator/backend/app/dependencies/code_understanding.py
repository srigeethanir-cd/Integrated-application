"""FastAPI dependency providers for Stage 3."""

from typing import Annotated

from fastapi import Depends
from openai import OpenAI
from sqlalchemy.orm import Session

from app.agents.code_understanding.agent import CodeUnderstandingAgent
from app.agents.code_understanding.client import (
    GroqStructuredOutputClient,
    ResilientStructuredOutputClient,
)
from app.agents.test_generation.test_generation_agent import TestGenerationAgent
from app.agents.semantic_verification.agent import TestVerificationAgent
from app.agents.quality_evaluation.agent import TestQualityEvaluationAgent
from app.core.config import settings, validate_llm_provider_configuration
from app.database.repositories.code_understanding_repository import (
    CodeUnderstandingRepository,
)
from app.database.repositories.security_scan_repository import SecurityScanRepository
from app.database.session import get_db_session
from app.dependencies.dependency import DependencyRepositoryDependency
from app.dependencies.project import (
    ProjectRepositoryDependency,
    StorageServiceDependency,
)
from app.services.code_understanding.code_understanding_service import (
    CodeUnderstandingService,
)
from app.services.quality_loop_service import QualityLoopService
from app.services.runtime.runtime_preparation_service import RuntimePreparationService
from app.infrastructure.redis import CacheManager, get_cache_manager


def get_code_understanding_repository(
    session: Annotated[Session, Depends(get_db_session)],
) -> CodeUnderstandingRepository:
    return CodeUnderstandingRepository(session)


CodeUnderstandingRepositoryDependency = Annotated[
    CodeUnderstandingRepository,
    Depends(get_code_understanding_repository),
]


def _get_structured_output_client(
    *, max_completion_tokens: int | None = None
) -> ResilientStructuredOutputClient:
    validate_llm_provider_configuration(settings)
    providers = {}
    if (
        settings.groq_api_key is not None
        and settings.groq_api_key.get_secret_value().strip()
    ):
        providers["groq"] = GroqStructuredOutputClient(
            client=OpenAI(
                api_key=settings.groq_api_key.get_secret_value(),
                base_url="https://api.groq.com/openai/v1",
                max_retries=0,
            ),
            model=settings.groq_model,
            max_completion_tokens=max_completion_tokens,
            model_max_output_tokens=settings.groq_model_max_output_tokens,
            tokens_per_minute=settings.groq_tokens_per_minute,
            requests_per_minute=settings.groq_requests_per_minute,
            token_reserve=settings.llm_token_preflight_reserve,
            completion_estimation_safety_margin=(
                settings.stage3_completion_estimation_safety_margin
            ),
        )
    if (
        settings.cerebras_api_key is not None
        and settings.cerebras_api_key.get_secret_value().strip()
    ):
        providers["cerebras"] = GroqStructuredOutputClient(
            client=OpenAI(
                api_key=settings.cerebras_api_key.get_secret_value(),
                base_url="https://api.cerebras.ai/v1",
                max_retries=0,
            ),
            model=settings.cerebras_model,
            max_completion_tokens=max_completion_tokens,
            model_max_output_tokens=settings.cerebras_model_max_output_tokens,
            tokens_per_minute=settings.cerebras_tokens_per_minute,
            requests_per_minute=settings.cerebras_requests_per_minute,
            token_reserve=settings.llm_token_preflight_reserve,
            completion_estimation_safety_margin=(
                settings.stage3_completion_estimation_safety_margin
            ),
        )
    primary = providers.get(settings.primary_llm_provider)
    if primary is None:
        raise RuntimeError(
            f"{settings.primary_llm_provider.upper()}_API_KEY is required"
        )
    fallback = (
        providers.get(settings.fallback_llm_provider)
        if settings.fallback_llm_provider != settings.primary_llm_provider
        else None
    )
    return ResilientStructuredOutputClient(
        primary,
        fallback,
        primary_name=settings.primary_llm_provider,
        fallback_name=settings.fallback_llm_provider,
        max_attempts=settings.max_provider_retries + 1,
        retry_base_delay=settings.test_verification_retry_base_delay,
        max_retry_delay=settings.test_verification_max_retry_delay,
        failover_threshold_seconds=settings.provider_failover_threshold_seconds,
        enable_failover=settings.enable_provider_failover,
    )


def get_code_understanding_agent() -> CodeUnderstandingAgent:
    """Build deterministic Stage 3A without requiring an LLM provider."""
    return CodeUnderstandingAgent()


CodeUnderstandingAgentDependency = Annotated[
    CodeUnderstandingAgent,
    Depends(get_code_understanding_agent),
]


def get_test_generation_agent() -> TestGenerationAgent:
    return TestGenerationAgent(
        model_name=settings.groq_model,
        deterministic_mode=True,
        max_batch_functions=settings.test_generation_batch_max_functions,
        estimated_tokens_per_case=settings.test_generation_estimated_tokens_per_case,
        safe_output_tokens=settings.test_generation_safe_output_tokens,
    )


TestGenerationAgentDependency = Annotated[
    TestGenerationAgent,
    Depends(get_test_generation_agent),
]


def get_test_verification_agent() -> TestVerificationAgent:
    return TestVerificationAgent(
        model_name=settings.groq_model,
        max_provider_attempts=1,
        retry_base_delay=settings.test_verification_retry_base_delay,
        max_retry_delay=settings.test_verification_max_retry_delay,
        rule_confidence_threshold=settings.test_verification_rule_confidence_threshold,
    )


TestVerificationAgentDependency = Annotated[
    TestVerificationAgent,
    Depends(get_test_verification_agent),
]


def get_test_quality_evaluation_agent() -> TestQualityEvaluationAgent:
    return TestQualityEvaluationAgent(
        model_name=settings.groq_model
    )


TestQualityEvaluationAgentDependency = Annotated[
    TestQualityEvaluationAgent,
    Depends(get_test_quality_evaluation_agent),
]


def get_quality_loop_service(
    generator: TestGenerationAgentDependency,
    verifier: TestVerificationAgentDependency,
    evaluator: TestQualityEvaluationAgentDependency,
) -> QualityLoopService:
    return QualityLoopService(
        generator,
        verifier,
        evaluator,
        threshold=settings.test_quality_threshold,
        max_iterations=settings.test_quality_max_iterations,
        minimum_improvement_delta=settings.test_quality_minimum_improvement_delta,
    )


QualityLoopServiceDependency = Annotated[
    QualityLoopService,
    Depends(get_quality_loop_service),
]


def get_code_understanding_service(
    session: Annotated[Session, Depends(get_db_session)],
    project_repository: ProjectRepositoryDependency,
    dependency_repository: DependencyRepositoryDependency,
    code_understanding_repository: CodeUnderstandingRepositoryDependency,
    storage_service: StorageServiceDependency,
    agent: CodeUnderstandingAgentDependency,
    test_generation_agent: TestGenerationAgentDependency,
    test_verification_agent: TestVerificationAgentDependency,
    quality_evaluation_agent: TestQualityEvaluationAgentDependency,
    quality_loop_service: QualityLoopServiceDependency,
    cache_manager: Annotated[CacheManager, Depends(get_cache_manager)],
) -> CodeUnderstandingService:
    return CodeUnderstandingService(
        project_repository=project_repository,
        dependency_repository=dependency_repository,
        code_understanding_repository=code_understanding_repository,
        storage_service=storage_service,
        agent=agent,
        model_name=settings.groq_model,
        max_file_characters=settings.code_understanding_max_file_characters,
        max_total_characters=settings.code_understanding_max_total_characters,
        test_generation_agent=test_generation_agent,
        test_verification_agent=test_verification_agent,
        quality_evaluation_agent=quality_evaluation_agent,
        quality_loop_service=quality_loop_service,
        runtime_preparation_service=RuntimePreparationService(),
        quality_threshold=settings.test_quality_threshold,
        cache_manager=cache_manager,
        stage3_provider_cache_ttl=settings.stage3_provider_cache_ttl_seconds,
        enable_stage3_cache=settings.enable_stage3_cache,
        stage3_enrichment_cache_ttl=settings.stage3_enrichment_cache_ttl_seconds,
        runtime_preparation_cache_ttl=settings.runtime_preparation_cache_ttl_seconds,
        checkpoint_cache_ttl=settings.pipeline_checkpoint_cache_ttl_seconds,
        security_scan_repository=SecurityScanRepository(session),
    )


CodeUnderstandingServiceDependency = Annotated[
    CodeUnderstandingService,
    Depends(get_code_understanding_service),
]
