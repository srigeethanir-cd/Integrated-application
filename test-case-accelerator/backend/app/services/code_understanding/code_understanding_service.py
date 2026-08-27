"""Application service orchestrating Stage 3 code understanding."""

from __future__ import annotations

import uuid
import logging
import hashlib
import json
import time
from pathlib import Path

from sqlalchemy.exc import SQLAlchemyError

from app.agents.code_understanding.agent import (
    CodeUnderstandingAgent,
    CodeUnderstandingContext,
    SourceFileContext,
)
from app.agents.test_generation.test_generation_agent import TestGenerationAgent
from app.agents.semantic_verification.agent import TestVerificationAgent
from app.schemas.test_case import TestCase
from app.schemas.enums import Category
from app.schemas.test_quality import QualityEvaluation, QualityLoopResult
from app.agents.quality_evaluation.agent import TestQualityEvaluationAgent
from app.services.quality_loop_service import QualityLoopService
from app.services.runtime.runtime_preparation_service import (
    RuntimePreparationService,
)
from app.database.models.code_understanding import CodeUnderstandingRun, CodeUnderstandingStatus
from app.database.repositories.code_understanding_repository import (
    CodeUnderstandingRepository,
)
from app.database.repositories.dependency_repository import DependencyRepository
from app.database.repositories.project_repository import ProjectRepository
from app.prompts.code_understanding import PROMPT_VERSION
from app.services.ingestion.storage_service import StorageService
from app.infrastructure.redis import CacheKeyBuilder, CacheManager, CacheTTL
from app.infrastructure.artifact_version import (
    ARTIFACT_VERSION_KEY,
    SEMANTIC_CONTRACT_VERSION,
    artifact_version_manifest,
    fingerprint,
)

logger = logging.getLogger(__name__)


class CodeUnderstandingError(RuntimeError):
    """Base exception for invalid or failed Stage 3 operations."""


class ProjectNotFoundError(CodeUnderstandingError):
    """Raised when the requested Stage 1 project does not exist."""


class DependencyRunNotFoundError(CodeUnderstandingError):
    """Raised when the requested Stage 2 run does not exist."""


class DependencyRunNotReadyError(CodeUnderstandingError):
    """Raised when Stage 2 is incomplete or belongs to another project."""


class InvalidSourcePathError(CodeUnderstandingError):
    """Raised when persisted source metadata escapes managed storage."""


class CodeUnderstandingRunNotFoundError(CodeUnderstandingError):
    """Raised when a later stage references an unknown Stage 3 run."""


class CodeUnderstandingRunNotReadyError(CodeUnderstandingError):
    """Raised when a Stage 3 run cannot be consumed by a later stage."""


class CodeUnderstandingService:
    """Coordinate Stage 2 input loading, agent execution, and persistence."""

    def __init__(
        self,
        project_repository: ProjectRepository,
        dependency_repository: DependencyRepository,
        code_understanding_repository: CodeUnderstandingRepository,
        storage_service: StorageService,
        agent: CodeUnderstandingAgent,
        model_name: str,
        prompt_version: str = PROMPT_VERSION,
        max_file_characters: int = 2_500,
        max_total_characters: int = 10_000,
        test_generation_agent: TestGenerationAgent | None = None,
        test_verification_agent: TestVerificationAgent | None = None,
        quality_evaluation_agent: TestQualityEvaluationAgent | None = None,
        quality_loop_service: QualityLoopService | None = None,
        runtime_preparation_service: RuntimePreparationService | None = None,
        quality_threshold: float = 90,
        cache_manager: CacheManager | None = None,
        enable_stage3_cache: bool = True,
        stage3_provider_cache_ttl: int = int(CacheTTL.CODE_UNDERSTANDING_CACHE),
        stage3_enrichment_cache_ttl: int = int(CacheTTL.CODE_UNDERSTANDING_CACHE),
        runtime_preparation_cache_ttl: int = int(CacheTTL.QUALITY_CACHE),
        checkpoint_cache_ttl: int = int(CacheTTL.QUALITY_CACHE),
        security_scan_repository=None,
    ) -> None:
        if max_file_characters <= 0 or max_total_characters <= 0:
            raise ValueError("Code-understanding context limits must be positive")

        self._project_repository = project_repository
        self._dependency_repository = dependency_repository
        self._code_understanding_repository = code_understanding_repository
        self._storage_service = storage_service
        self._agent = agent
        self._test_generation_agent = test_generation_agent
        self._test_verification_agent = test_verification_agent
        self._quality_evaluation_agent = quality_evaluation_agent
        self._quality_loop_service = quality_loop_service
        self._runtime_preparation_service = (
            runtime_preparation_service or RuntimePreparationService()
        )
        self._quality_threshold = quality_threshold
        self._model_name = model_name
        self._prompt_version = prompt_version
        self._max_file_characters = max_file_characters
        self._max_total_characters = max_total_characters
        self._cache_manager = cache_manager
        self._enable_stage3_cache = enable_stage3_cache
        self._stage3_provider_cache_ttl = stage3_provider_cache_ttl
        self._stage3_enrichment_cache_ttl = stage3_enrichment_cache_ttl
        self._runtime_preparation_cache_ttl = runtime_preparation_cache_ttl
        self._checkpoint_cache_ttl = checkpoint_cache_ttl
        self._security_scan_repository = security_scan_repository

    def run(
        self,
        project_id: uuid.UUID,
        dependency_run_id: uuid.UUID,
    ) -> CodeUnderstandingRun:
        """Run the backward-compatible Stage 3 -> 4 -> 5 pipeline."""
        return self._execute_understanding(
            project_id, dependency_run_id, include_pipeline=True
        )

    def retry(self, run_id: uuid.UUID) -> CodeUnderstandingRun:
        """Resume a failed pipeline run from its first incomplete stage."""
        run = self._code_understanding_repository.get_by_id(run_id)
        if run is None:
            raise CodeUnderstandingRunNotFoundError(
                "Pipeline run not found"
            )
        if run.status != CodeUnderstandingStatus.FAILED:
            raise CodeUnderstandingRunNotReadyError(
                "Only failed pipeline runs can be retried"
            )
        self._code_understanding_repository.prepare_retry(run)
        return self._execute_understanding(
            run.project_id,
            run.dependency_run_id,
            include_pipeline=True,
            resume_run_id=run.id,
        )

    def force_rerun(
        self,
        project_id: uuid.UUID,
        dependency_run_id: uuid.UUID,
        *,
        start_stage: str,
    ) -> CodeUnderstandingRun:
        """Rerun a completed pipeline from an explicitly selected stage."""
        if start_stage != "test_generation":
            raise CodeUnderstandingRunNotReadyError(
                "Forced rerun currently supports test_generation only"
            )
        runs = self._code_understanding_repository.get_by_dependency_run_id(
            dependency_run_id
        )
        run = next(
            (
                item for item in runs
                if item.project_id == project_id
                and item.status == CodeUnderstandingStatus.COMPLETED
            ),
            None,
        )
        if run is None:
            raise CodeUnderstandingRunNotReadyError(
                "A completed pipeline run is required for forced rerun"
            )
        invalidated = [
            "test_generation",
            "test_verification",
            "quality_evaluation",
            "quality_optimization",
            "quality_checkpoint",
            "runtime_execution_plan",
        ]
        logger.info("Starting rerun from Stage 4")
        logger.info("Invalidated: %s", ", ".join(invalidated))
        self._code_understanding_repository.prepare_forced_rerun(
            run, start_stage="stage_4"
        )
        regenerated = self._execute_understanding(
            run.project_id,
            run.dependency_run_id,
            include_pipeline=True,
            resume_run_id=run.id,
        )
        logger.info(
            "Regenerated: test_generation, test_verification, "
            "quality_evaluation, quality_optimization, runtime_execution_plan"
        )
        return regenerated

    def understand(
        self,
        project_id: uuid.UUID,
        dependency_run_id: uuid.UUID,
    ) -> CodeUnderstandingRun:
        """Run and persist Stage 3 only."""
        return self._execute_understanding(
            project_id, dependency_run_id, include_pipeline=False
        )

    def _execute_understanding(
        self,
        project_id: uuid.UUID,
        dependency_run_id: uuid.UUID,
        *,
        include_pipeline: bool,
        resume_run_id: uuid.UUID | None = None,
    ) -> CodeUnderstandingRun:
        stage3_started = time.perf_counter()
        project = self._project_repository.get_by_id(project_id, for_update=True)
        if project is None:
            raise ProjectNotFoundError("Project not found")

        dependency_run = self._dependency_repository.get_by_id(dependency_run_id)
        if dependency_run is None:
            raise DependencyRunNotFoundError("Dependency run not found")
        if dependency_run.project_id != project_id:
            raise DependencyRunNotReadyError(
                "Dependency run does not belong to the requested project"
            )
        if dependency_run.status != "completed":
            raise DependencyRunNotReadyError(
                "Dependency run must be completed before code understanding"
            )

        # Check if we can resume an existing run (idempotency check)
        runs = self._code_understanding_repository.get_by_dependency_run_id(dependency_run_id)
        active_artifact_version = self._artifact_version_manifest(
            include_pipeline=include_pipeline
        )
        if resume_run_id is not None:
            run = self._code_understanding_repository.get_by_id(resume_run_id)
            if run is None:
                raise CodeUnderstandingRunNotFoundError("Pipeline run not found")
            if not self._artifact_version_matches(run, active_artifact_version):
                self._invalidate_stale_artifacts(
                    run, project_id, active_artifact_version
                )
                stage3_payload = {}
            else:
                stage3_payload = dict(run.result or {})
        elif runs:
            run = runs[0]
            if run.status == CodeUnderstandingStatus.RUNNING:
                raise CodeUnderstandingError(
                    "Workflow resume is already running for this project"
                )
            version_matches = self._artifact_version_matches(
                run, active_artifact_version
            )
            if run.status == CodeUnderstandingStatus.COMPLETED and version_matches:
                logger.info(
                    "CACHE HIT artifact=pipeline project_id=%s run_id=%s",
                    project_id,
                    run.id,
                )
                return run
            if not version_matches:
                legacy_payload = dict(run.result or {})
                if (
                    ARTIFACT_VERSION_KEY not in legacy_payload
                    and "project_summary" in legacy_payload
                ):
                    self._code_understanding_repository.prepare_forced_rerun(
                        run, start_stage="stage_4"
                    )
                    stage3_payload = legacy_payload
                else:
                    self._invalidate_stale_artifacts(
                        run, project_id, active_artifact_version
                    )
                    stage3_payload = {}
            else:
                self._code_understanding_repository.mark_running(run)
                stage3_payload = dict(run.result or {})
        else:
            run = self._code_understanding_repository.create_run(
                project_id=project_id,
                dependency_run_id=dependency_run_id,
                model_name=self._model_name,
                prompt_version=self._prompt_version,
            )
            self._code_understanding_repository.mark_running(run)
            stage3_payload = {}

        source_directory = self._resolve_source_directory(
            project_id,
            project.storage_path,
        )
        cache_key: str | None = None
        content_hash: str | None = None
        if (
            self._cache_manager is not None
            and getattr(self, "_enable_stage3_cache", True)
        ):
            content_hash = self._source_content_hash(
                project_id, source_directory, dependency_run.files
            )
            content_hash = fingerprint({
                "source": content_hash,
                "semantic": active_artifact_version["semantic"],
            })
            cache_key = CacheKeyBuilder.code_understanding_content(
                project_id, content_hash
            )
            if not include_pipeline:
                cached = self._cache_manager.get(cache_key)
                cached_run = self._load_cached_run(cached)
                if (
                    cached_run is not None
                    and self._artifact_version_matches(
                        cached_run, active_artifact_version
                    )
                ):
                    logger.info(
                        "CACHE HIT stage=code-understanding project_id=%s "
                        "execution_seconds=%.3f",
                        project_id, time.perf_counter() - stage3_started,
                    )
                    return cached_run
                if cached_run is not None:
                    logger.warning(
                        "ARTIFACT VERSION MISMATCH source=redis "
                        "project_id=%s run_id=%s",
                        project_id,
                        cached_run.id,
                    )
                    self._cache_manager.delete(cache_key)
                    logger.info(
                        "CACHE INVALIDATED stage=code-understanding "
                        "project_id=%s",
                        project_id,
                    )
                logger.info(
                    "CACHE MISS stage=code-understanding project_id=%s",
                    project_id,
                )

        current_stage = "stage_3"
        try:
            # Build context lazily only when needed by stage 3 or stage 5/6
            context = None

            # ---- Stage 3: Code Understanding ----
            if stage3_payload and "project_summary" in stage3_payload:
                logger.info("Skipping completed Stage 3.")
                from app.agents.code_understanding.agent import CodeUnderstandingResult
                stage3_clean = {
                    key: value for key, value in stage3_payload.items()
                    if key not in (
                        "test_generation", "test_verification",
                        "quality_evaluation", "quality_optimization",
                        "quality_checkpoint", "runtime_execution_plan",
                        ARTIFACT_VERSION_KEY,
                    )
                }
                result = CodeUnderstandingResult.model_validate(stage3_clean)
            else:
                logger.info("Continuing to Stage 3.")
                self._dependency_repository.save_analysis_status(dependency_run_id, 3, "code_understanding", "running")
                context = self._build_context(
                    project_id=project_id,
                    dependency_run_id=dependency_run_id,
                    source_directory=source_directory,
                    discovered_files=dependency_run.files,
                )
                enriched_key = (
                    CacheKeyBuilder.enriched_stage3(project_id, content_hash)
                    if content_hash is not None else None
                )
                cached_enriched = (
                    self._cache_manager.get(enriched_key)
                    if (
                        getattr(self, "_enable_stage3_cache", True)
                        and self._cache_manager is not None
                        and enriched_key is not None
                    )
                    else None
                )
                if isinstance(cached_enriched, dict):
                    try:
                        result = CodeUnderstandingResult.model_validate(
                            cached_enriched
                        )
                    except Exception:
                        logger.warning(
                            "stage3_cache event=miss reason=invalid_cached_output "
                            "project_id=%s",
                            project_id,
                        )
                        cached_enriched = None
                    else:
                        logger.info(
                            "stage3_cache event=hit reuse=true artifact=enriched "
                            "project_id=%s",
                            project_id,
                        )
                if not isinstance(cached_enriched, dict):
                    logger.info(
                        "stage3_cache event=miss reuse=false artifact=enriched "
                        "project_id=%s",
                        project_id,
                    )
                    artifact_method = getattr(
                        type(self._agent), "analyze_with_artifacts", None
                    )
                    if callable(artifact_method):
                        provider_payload, result = artifact_method(
                            self._agent,
                            context,
                            max_file_characters=self._max_file_characters,
                            max_total_characters=self._max_total_characters,
                        )
                    else:
                        result = self._agent.analyze(
                            context,
                            max_file_characters=self._max_file_characters,
                            max_total_characters=self._max_total_characters,
                        )
                        provider_payload = None
                    if (
                        getattr(self, "_enable_stage3_cache", True)
                        and self._cache_manager is not None
                        and content_hash is not None
                    ):
                        if provider_payload is not None:
                            self._cache_manager.set(
                                CacheKeyBuilder.provider_response(
                                    project_id, content_hash
                                ),
                                provider_payload,
                                ttl=getattr(self, "_stage3_provider_cache_ttl", int(CacheTTL.CODE_UNDERSTANDING_CACHE)),
                            )
                        self._cache_manager.set(
                            CacheKeyBuilder.enriched_stage3(
                                project_id, content_hash
                            ),
                            result.model_dump(mode="json"),
                            ttl=getattr(self, "_stage3_enrichment_cache_ttl", int(CacheTTL.CODE_UNDERSTANDING_CACHE)),
                        )
                stage3_payload = result.model_dump(mode="json")
                self._code_understanding_repository.save_stage3_result(run, stage3_payload)
                self._dependency_repository.save_analysis_status(dependency_run_id, 3, "code_understanding", "completed")
            logger.info(
                "stage3_execution completed=true cache_enabled=%s "
                "execution_seconds=%.3f project_id=%s",
                getattr(self, "_enable_stage3_cache", True),
                time.perf_counter() - stage3_started,
                project_id,
            )

            # ---- Stage 4: Test Generation ----
            test_gen_agent = self._test_generation_agent if include_pipeline else None
            stage4_output = None
            if test_gen_agent is not None:
                current_stage = "stage_4"
                persisted_generation = stage3_payload.get("test_generation")
                current_generation = (
                    persisted_generation is not None
                    and test_gen_agent.is_current_output(
                        persisted_generation, stage3_payload
                    )
                )
                if current_generation:
                    logger.info("Skipping completed Stage 4.")
                    stage4_output = persisted_generation
                else:
                    if persisted_generation is not None:
                        logger.info(
                            "Invalidating stale Stage 4 output: lifecycle planner "
                            "version is missing or outdated."
                        )
                        for key in (
                            "test_verification", "quality_evaluation",
                            "quality_optimization", "quality_checkpoint",
                            "runtime_execution_plan",
                        ):
                            stage3_payload.pop(key, None)
                    logger.info("Continuing to Stage 4.")
                    self._dependency_repository.save_analysis_status(dependency_run_id, 4, "test_generation", "running")
                    stage4_output = test_gen_agent.generate(stage3_payload)
                    stage3_payload["test_generation"] = stage4_output
                    self._code_understanding_repository.save_test_generation(run, stage4_output)
                    self._dependency_repository.save_analysis_status(dependency_run_id, 4, "test_generation", "completed")
                self._log_test_execution_metadata("stage4", stage4_output)

            # ---- Stage 5 & 6: Test Verification & Quality Loop ----
            if include_pipeline and stage4_output is not None:
                current_stage = "stage_5"
                if stage3_payload.get("quality_optimization") is not None:
                    logger.info("Skipping completed Stage 5 & 6.")
                    if stage3_payload.get("runtime_execution_plan") is None:
                        current_stage = "runtime_preparation"
                        optimized = QualityLoopResult.model_validate(
                            stage3_payload["quality_optimization"]
                        )
                        stage3_payload["runtime_execution_plan"] = (
                            self._prepare_runtime_execution_plan(
                                optimized.optimized_test_suite,
                                result.model_dump(mode="json"),
                                project_id=project_id,
                            )
                        )
                        self._code_understanding_repository.save_runtime_execution_plan(
                            run, stage3_payload["runtime_execution_plan"]
                        )
                elif self._quality_loop_service is not None:
                    current_stage = "stage_6"
                    logger.info("Continuing to Stage 5 & 6 (Quality Loop).")
                    self._dependency_repository.save_analysis_status(dependency_run_id, 5, "test_verification", "running")
                    self._dependency_repository.save_analysis_status(dependency_run_id, 6, "quality_optimization", "running")
                    
                    if context is None:
                        context = self._build_context(
                            project_id=project_id,
                            dependency_run_id=dependency_run_id,
                            source_directory=source_directory,
                            discovered_files=dependency_run.files,
                        )
                    quality = self._quality_loop_service.run(
                        result.model_dump(mode="json"),
                        [item.model_dump(mode="json") for item in context.files],
                        stage4_output,
                        repo_root=str(source_directory),
                    )
                    stage3_payload["test_generation"] = (
                        quality.test_generation.model_dump(mode="json")
                    )
                    stage3_payload["test_verification"] = (
                        quality.test_verification.model_dump(mode="json")
                    )
                    stage3_payload["quality_evaluation"] = (
                        quality.quality_evaluation.model_dump(mode="json")
                    )
                    stage3_payload["quality_optimization"] = quality.model_dump(
                        mode="json"
                    )
                    self._log_test_execution_metadata(
                        "stage5_quality_optimized",
                        {"generated_test_cases": [
                            item.model_dump(mode="json")
                            for item in quality.optimized_test_suite
                        ]},
                    )
                    self._code_understanding_repository.save_quality_optimization(
                        run, stage3_payload["quality_optimization"]
                    )
                    current_stage = "runtime_preparation"
                    stage3_payload["runtime_execution_plan"] = (
                        self._prepare_runtime_execution_plan(
                            quality.optimized_test_suite,
                            result.model_dump(mode="json"),
                            project_id=project_id,
                        )
                    )
                    self._code_understanding_repository.save_runtime_execution_plan(
                        run, stage3_payload["runtime_execution_plan"]
                    )
                    
                    self._dependency_repository.save_analysis_status(dependency_run_id, 5, "test_verification", "completed")
                    self._dependency_repository.save_analysis_status(dependency_run_id, 6, "quality_optimization", "completed")
                elif self._test_verification_agent is not None:
                    if stage3_payload.get("test_verification") is not None:
                        logger.info("Skipping completed Stage 5.")
                    else:
                        logger.info("Continuing to Stage 5.")
                        self._dependency_repository.save_analysis_status(dependency_run_id, 5, "test_verification", "running")
                        if context is None:
                            context = self._build_context(
                                project_id=project_id,
                                dependency_run_id=dependency_run_id,
                                source_directory=source_directory,
                                discovered_files=dependency_run.files,
                            )
                        stage3_payload["test_verification"] = (
                            self._test_verification_agent.verify(
                                stage4_output["generated_test_cases"],
                                result.model_dump(mode="json"),
                                [item.model_dump(mode="json") for item in context.files],
                                repo_root=str(source_directory),
                            )
                        )
                        self._code_understanding_repository.save_test_verification(run, stage3_payload["test_verification"])
                        self._dependency_repository.save_analysis_status(dependency_run_id, 5, "test_verification", "completed")

            stage3_payload[ARTIFACT_VERSION_KEY] = active_artifact_version
            completed_run = self._code_understanding_repository.complete(
                run,
                stage3_payload,
            )
            if (
                getattr(self, "_enable_stage3_cache", True)
                and cache_key is not None
                and self._cache_manager is not None
            ):
                stored = self._cache_manager.set(
                    cache_key,
                    {
                        "run_id": str(completed_run.id),
                        "status": str(completed_run.status),
                        "result": completed_run.result,
                    },
                    ttl=int(CacheTTL.CODE_UNDERSTANDING_CACHE),
                )
                if stored:
                    logger.info(
                        "CACHE STORE stage=code-understanding project_id=%s",
                        project_id,
                    )
            return completed_run
        except Exception as error:
            self._safe_fail_run(run, error, failed_stage=current_stage)
            raise

    def generate_test_cases(
        self,
        project_id: uuid.UUID,
        code_understanding_run_id: uuid.UUID,
    ) -> dict:
        """Run Stage 4 from a completed, project-owned Stage 3 run."""
        stage3_payload, run = self._load_stage3_artifact(
            project_id, code_understanding_run_id
        )
        if self._test_generation_agent is None:
            raise CodeUnderstandingRunNotReadyError("Test generation is not configured")
        cache_manager = getattr(self, "_cache_manager", None)
        cache_key = self._generation_cache_key(
            project_id, code_understanding_run_id, run, stage3_payload
        ) if cache_manager is not None else None
        if cache_key is not None:
            cached = cache_manager.get(cache_key)
            if (
                self._is_completed_generation(cached)
                and self._test_generation_agent.is_current_output(
                    cached, stage3_payload
                )
            ):
                logger.info("CACHE HIT stage=test-generation project_id=%s", project_id)
                # PostgreSQL remains authoritative even when computation is skipped.
                self._code_understanding_repository.save_test_generation(run, cached)
                return cached
            logger.info("CACHE MISS stage=test-generation project_id=%s", project_id)
        try:
            generation = self._test_generation_agent.generate(stage3_payload)
        except Exception as error:
            self._safe_fail_run(run, error, failed_stage="stage_4")
            raise
        self._code_understanding_repository.save_test_generation(run, generation)
        if (
            cache_key is not None
            and cache_manager is not None
            and self._is_completed_generation(generation)
        ):
            if cache_manager.set(
                cache_key,
                generation,
                ttl=int(CacheTTL.TEST_GENERATION_CACHE),
            ):
                logger.info(
                    "CACHE STORE stage=test-generation project_id=%s", project_id
                )
        return generation

    def retry_test_generation(
        self,
        project_id: uuid.UUID,
        code_understanding_run_id: uuid.UUID,
    ) -> dict:
        """Retry only Stage 4 while preserving the completed Stage 3 artifact."""
        run = self._code_understanding_repository.get_by_id(
            code_understanding_run_id
        )
        if run is None or run.project_id != project_id:
            raise CodeUnderstandingRunNotFoundError(
                "Code-understanding run not found"
            )
        if (
            run.status != CodeUnderstandingStatus.FAILED
            or run.failed_stage != "stage_4"
        ):
            raise CodeUnderstandingRunNotReadyError(
                "Only a failed Stage 4 run can be retried"
            )
        preserved = dict(run.result or {})
        self._code_understanding_repository.prepare_retry(run)
        run.failed_stage = None
        run.failure_reason = None
        self._code_understanding_repository.complete(run, preserved)
        return self.generate_test_cases(project_id, code_understanding_run_id)

    @staticmethod
    def _log_test_execution_metadata(stage: str, generation: object) -> None:
        if not isinstance(generation, dict):
            return
        cases = generation.get("generated_test_cases", [])
        logger.info(
            "Pipeline test metadata stage=%s cases=%s",
            stage,
            [
                {
                    "test_case_id": case.get("id"),
                    "path_parameters": trace.get("path_parameters"),
                    "dependency_metadata": trace.get("depends_on"),
                    "capture_metadata": trace.get("identifier_fields"),
                    "payload": trace.get("request_payload"),
                    "order": index,
                }
                for index, case in enumerate(cases)
                if isinstance(case, dict)
                and isinstance((trace := case.get("traceability")), dict)
                and trace.get("method")
            ],
        )

    def _generation_cache_key(
        self,
        project_id: uuid.UUID,
        code_understanding_run_id: uuid.UUID,
        run: CodeUnderstandingRun,
        stage3_payload: dict,
    ) -> str | None:
        """Build a deterministic Stage 4 key, falling back safely on errors."""
        try:
            project = self._project_repository.get_by_id(project_id)
            dependency_run = self._dependency_repository.get_by_id(
                run.dependency_run_id
            )
            if project is None or dependency_run is None:
                return None
            source_directory = self._resolve_source_directory(
                project_id, project.storage_path
            )
            source_hash = self._source_content_hash(
                project_id, source_directory, dependency_run.files
            )
            inputs = {
                "source_hash": source_hash,
                "stage3": stage3_payload,
                "stage3_prompt_version": run.prompt_version,
                "generation": self._test_generation_agent.cache_fingerprint(),
            }
            serialized = json.dumps(
                inputs, sort_keys=True, separators=(",", ":"), ensure_ascii=False
            ).encode("utf-8")
            generation_hash = hashlib.sha256(serialized).hexdigest()
            return CacheKeyBuilder.test_generation_content(
                project_id, code_understanding_run_id, generation_hash
            )
        except Exception:
            logger.exception(
                "CACHE ERROR stage=test-generation operation=key-build project_id=%s",
                project_id,
            )
            return None

    @staticmethod
    def _is_completed_generation(value: object) -> bool:
        """Return whether a value is a complete, cache-eligible generation suite."""
        return (
            isinstance(value, dict)
            and isinstance(value.get("generated_test_cases"), list)
            and value.get("generation_status", "complete") == "complete"
        )

    def verify_test_cases(
        self,
        project_id: uuid.UUID,
        code_understanding_run_id: uuid.UUID,
        test_cases: list[TestCase],
    ) -> dict:
        """Run Stage 5 independently from Stage 3 and supplied Stage 4 cases."""
        stage3_payload, run = self._load_stage3_artifact(
            project_id, code_understanding_run_id
        )
        if self._test_verification_agent is None:
            raise CodeUnderstandingRunNotReadyError(
                "Test verification is not configured"
            )
        project = self._project_repository.get_by_id(project_id)
        if project is None:
            raise ProjectNotFoundError("Project not found")
        dependency_run = self._dependency_repository.get_by_id(run.dependency_run_id)
        if dependency_run is None or dependency_run.status != "completed":
            raise DependencyRunNotReadyError(
                "Dependency run must be completed before test verification"
            )
        source_directory = self._resolve_source_directory(
            project_id, project.storage_path
        )
        context = self._build_context(
            project_id=project_id,
            dependency_run_id=run.dependency_run_id,
            source_directory=source_directory,
            discovered_files=dependency_run.files,
        )
        source_files = [item.model_dump(mode="json") for item in context.files]
        cache_manager = getattr(self, "_cache_manager", None)
        cache_key = (
            self._verification_cache_key(
                project_id,
                code_understanding_run_id,
                test_cases,
                stage3_payload,
                source_files,
            )
            if cache_manager is not None
            else None
        )
        if cache_key is not None:
            cached = cache_manager.get(cache_key)
            if self._is_completed_verification(cached):
                logger.info("CACHE HIT stage=verification project_id=%s", project_id)
                self._code_understanding_repository.save_test_verification(run, cached)
                return cached
            logger.info("CACHE MISS stage=verification project_id=%s", project_id)
        try:
            verification = self._test_verification_agent.verify(
                test_cases, stage3_payload, source_files
            )
        except Exception as error:
            self._safe_fail_run(run, error, failed_stage="stage_5")
            raise
        self._code_understanding_repository.save_test_verification(
            run,
            verification,
        )
        if (
            cache_key is not None
            and cache_manager is not None
            and self._is_completed_verification(verification)
        ):
            if cache_manager.set(
                cache_key, verification, ttl=int(CacheTTL.VERIFICATION_CACHE)
            ):
                logger.info("CACHE STORE stage=verification project_id=%s", project_id)
        return verification

    def _verification_cache_key(
        self,
        project_id: uuid.UUID,
        verification_run_id: uuid.UUID,
        test_cases: list[TestCase],
        stage3_payload: dict,
        source_files: list[dict],
    ) -> str | None:
        """Build a deterministic Stage 5 key, falling back safely on errors."""
        try:
            inputs = {
                "test_suite": [case.model_dump(mode="json") for case in test_cases],
                "stage3": stage3_payload,
                "source_files": source_files,
                "verification": self._test_verification_agent.cache_fingerprint(),
            }
            serialized = json.dumps(
                inputs, sort_keys=True, separators=(",", ":"), ensure_ascii=False
            ).encode("utf-8")
            verification_hash = hashlib.sha256(serialized).hexdigest()
            return CacheKeyBuilder.verification_content(
                project_id, verification_run_id, verification_hash
            )
        except Exception:
            logger.exception(
                "CACHE ERROR stage=verification operation=key-build project_id=%s",
                project_id,
            )
            return None

    @staticmethod
    def _is_completed_verification(value: object) -> bool:
        """Return whether verification completed without Partial or Failed cases."""
        if not isinstance(value, dict) or not isinstance(value.get("results"), list):
            return False
        summary = value.get("summary")
        return (
            isinstance(summary, dict)
            and summary.get("partial") == 0
            and summary.get("failed") == 0
            and summary.get("verified") == len(value["results"])
        )

    def evaluate_test_quality(
        self,
        project_id: uuid.UUID,
        code_understanding_run_id: uuid.UUID,
        test_cases: list[TestCase],
        verification: dict,
        *,
        threshold: float | None = None,
    ) -> QualityEvaluation:
        stage3_payload, _ = self._load_stage3_artifact(
            project_id, code_understanding_run_id
        )
        if self._quality_evaluation_agent is None:
            raise CodeUnderstandingRunNotReadyError(
                "Test quality evaluation is not configured"
            )
        return self._quality_evaluation_agent.evaluate(
            test_cases,
            verification,
            stage3_payload,
            threshold=self._quality_threshold if threshold is None else threshold,
            iteration=1,
        )

    def optimize_test_quality(
        self,
        project_id: uuid.UUID,
        code_understanding_run_id: uuid.UUID,
        test_cases: list[TestCase],
        verification: dict,
    ) -> QualityLoopResult:
        """Run the independent Stage 6 optimization loop from supplied Stage 5 data."""
        operation = "CodeUnderstandingRepository.get_by_id"
        try:
            stage3_payload, run = self._load_stage3_artifact(
                project_id, code_understanding_run_id
            )
            if self._quality_loop_service is None:
                raise CodeUnderstandingRunNotReadyError(
                    "Test quality optimization is not configured"
                )
            operation = "DependencyRepository.get_by_id/load_files"
            source_files = self._load_source_files(project_id, run)
            categories = len({case.category for case in test_cases})
            generation = {
                "generated_test_cases": [
                    case.model_dump(mode="json") for case in test_cases
                ],
                "coverage_summary": {
                    "requirement_coverage": 0.0,
                    "category_coverage": round(categories / len(tuple(Category)) * 100, 2),
                },
                "total_generated": len(test_cases),
                "total_after_deduplication": len(test_cases),
            }
            checkpoint_key = CacheKeyBuilder.quality_checkpoint(
                project_id, code_understanding_run_id
            )
            resume_state = (run.result or {}).get("quality_checkpoint")
            if resume_state is None and getattr(self, "_cache_manager", None):
                cached_checkpoint = self._cache_manager.get(checkpoint_key)
                if (
                    isinstance(cached_checkpoint, dict)
                    and (
                        "resume_point" in cached_checkpoint
                        or "next_iteration" in cached_checkpoint
                    )
                ):
                    resume_state = cached_checkpoint
            cache_manager = getattr(self, "_cache_manager", None)
            cache_key = (
                self._quality_cache_key(
                    project_id,
                    code_understanding_run_id,
                    test_cases,
                    verification,
                    stage3_payload,
                    source_files,
                )
                if cache_manager is not None and not resume_state
                else None
            )
            if cache_key is not None:
                cached = cache_manager.get(cache_key)
                cached_optimization = self._completed_quality_optimization(cached)
                if cached_optimization is not None:
                    logger.info("CACHE HIT stage=quality project_id=%s", project_id)
                    self._code_understanding_repository.save_quality_optimization(
                        run, cached_optimization.model_dump(mode="json")
                    )
                    operation = "RuntimePreparationService.prepare"
                    self._persist_runtime_execution_plan(
                        run, cached_optimization, stage3_payload,
                        project_id=project_id,
                    )
                    return cached_optimization
                logger.info("CACHE MISS stage=quality project_id=%s", project_id)
            if resume_state:
                logger.info(
                    "Resuming quality optimization run_id=%s resume_point=%s "
                    "iteration=%s",
                    run.id, resume_state.get("resume_point"),
                    resume_state.get("next_iteration"),
                )

            def persist_checkpoint(phase: str, payload: dict) -> None:
                logger.info(
                    "Persisting quality checkpoint run_id=%s resume_point=%s "
                    "iteration=%s phase=%s",
                    run.id, payload.get("resume_point"),
                    payload.get("next_iteration"), phase,
                )
                self._code_understanding_repository.save_quality_checkpoint(
                    run, payload
                )
                if getattr(self, "_cache_manager", None):
                    self._cache_manager.set(
                        checkpoint_key,
                        payload,
                        ttl=getattr(self, "_checkpoint_cache_ttl", int(CacheTTL.QUALITY_CACHE)),
                    )

            operation = "QualityLoopService.run"
            optimized = self._quality_loop_service.run(
                stage3_payload,
                source_files,
                generation,
                initial_verification=verification,
                resume_state=resume_state,
                checkpoint=persist_checkpoint,
            )
            operation = "CodeUnderstandingRepository.save_quality_optimization"
            self._code_understanding_repository.save_quality_optimization(
                run, optimized.model_dump(mode="json")
            )
            operation = "RuntimePreparationService.prepare"
            self._persist_runtime_execution_plan(
                run, optimized, stage3_payload, project_id=project_id
            )
            if (
                cache_key is not None
                and cache_manager is not None
                and optimized.processing_status == "completed"
            ):
                if cache_manager.set(
                    cache_key,
                    optimized.model_dump(mode="json"),
                    ttl=int(CacheTTL.QUALITY_CACHE),
                ):
                    logger.info("CACHE STORE stage=quality project_id=%s", project_id)
            return optimized
        except SQLAlchemyError as error:
            logger.exception(
                "Stage 6 database failure service=CodeUnderstandingService.%s "
                "operation=%s entity=CodeUnderstandingRun entity_id=%s",
                "optimize_test_quality",
                operation,
                code_understanding_run_id,
            )
            if "run" in locals():
                failed_stage = (
                    "runtime_preparation"
                    if operation == "RuntimePreparationService.prepare"
                    else "stage_6"
                )
                self._safe_fail_run(run, error, failed_stage=failed_stage)
            raise
        except Exception as error:
            if "run" in locals():
                failed_stage = (
                    "runtime_preparation"
                    if operation == "RuntimePreparationService.prepare"
                    else "stage_6"
                )
                self._safe_fail_run(run, error, failed_stage=failed_stage)
            raise

    def _persist_runtime_execution_plan(
        self,
        run: CodeUnderstandingRun,
        optimization: QualityLoopResult,
        stage3_payload: dict,
        *,
        project_id: uuid.UUID | None = None,
    ) -> None:
        optimization_payload = optimization.model_dump(mode="json")
        plan = self._prepare_runtime_execution_plan(
            optimization_payload.get("optimized_test_suite", []),
            stage3_payload,
            project_id=project_id,
        )
        self._code_understanding_repository.save_runtime_execution_plan(
            run, plan
        )

    def _prepare_runtime_execution_plan(
        self,
        optimized_test_suite: list[TestCase | dict],
        stage3_payload: dict,
        *,
        project_id: uuid.UUID | None = None,
    ) -> dict:
        cache_key = None
        if project_id is not None and getattr(self, "_cache_manager", None):
            serialized = json.dumps(
                {
                    "suite": [
                        item.model_dump(mode="json")
                        if hasattr(item, "model_dump") else item
                        for item in optimized_test_suite
                    ],
                    "stage3": stage3_payload,
                },
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            ).encode("utf-8")
            cache_key = CacheKeyBuilder.runtime_preparation(
                project_id, hashlib.sha256(serialized).hexdigest()
            )
            cached = self._cache_manager.get(cache_key)
            if isinstance(cached, dict):
                self._log_runtime_plan_metadata("runtime_plan_cache", cached)
                return cached
        service = getattr(
            self, "_runtime_preparation_service", None
        ) or RuntimePreparationService()
        plan = service.prepare(
            optimized_test_suite, stage3_payload
        ).model_dump(mode="json")
        self._log_runtime_plan_metadata("runtime_plan_prepared", plan)
        if cache_key is not None:
            self._cache_manager.set(
                cache_key, plan,
                ttl=getattr(self, "_runtime_preparation_cache_ttl", int(CacheTTL.QUALITY_CACHE)),
            )
        return plan

    @staticmethod
    def _log_runtime_plan_metadata(stage: str, plan: dict) -> None:
        logger.info(
            "Pipeline runtime-plan metadata stage=%s targets=%s",
            stage,
            [
                {
                    "test_case_id": target.get("test_case_id"),
                    "path_parameters": target.get("path_parameters"),
                    "dependency_metadata": (
                        target.get("traceability", {}).get("depends_on")
                        if isinstance(target.get("traceability"), dict) else None
                    ),
                    "capture_metadata": (
                        target.get("traceability", {}).get("identifier_fields")
                        if isinstance(target.get("traceability"), dict) else None
                    ),
                    "payload": target.get("request_payload"),
                    "order": index,
                }
                for index, target in enumerate(plan.get("targets", []))
                if isinstance(target, dict)
            ],
        )

    def _quality_cache_key(
        self,
        project_id: uuid.UUID,
        optimization_run_id: uuid.UUID,
        test_cases: list[TestCase],
        verification: dict,
        stage3_payload: dict,
        source_files: list[dict],
    ) -> str | None:
        """Build a deterministic Stage 6 key, falling back safely on errors."""
        try:
            verification_payload = (
                verification.model_dump(mode="json")
                if hasattr(verification, "model_dump")
                else verification
            )
            inputs = {
                "test_suite": [case.model_dump(mode="json") for case in test_cases],
                "verification": verification_payload,
                "stage3": stage3_payload,
                "source_files": source_files,
                "optimization": self._quality_loop_service.cache_fingerprint(),
            }
            serialized = json.dumps(
                inputs, sort_keys=True, separators=(",", ":"), ensure_ascii=False
            ).encode("utf-8")
            quality_hash = hashlib.sha256(serialized).hexdigest()
            return CacheKeyBuilder.quality_content(
                project_id, optimization_run_id, quality_hash
            )
        except Exception:
            logger.exception(
                "CACHE ERROR stage=quality operation=key-build project_id=%s",
                project_id,
            )
            return None

    @staticmethod
    def _completed_quality_optimization(
        value: object,
    ) -> QualityLoopResult | None:
        """Validate and return only completed, cache-eligible optimization output."""
        if not isinstance(value, dict) or value.get("processing_status") != "completed":
            return None
        try:
            return QualityLoopResult.model_validate(value)
        except Exception:
            logger.exception("CACHE ERROR stage=quality operation=deserialize")
            return None

    def _load_source_files(
        self, project_id: uuid.UUID, run: CodeUnderstandingRun
    ) -> list[dict]:
        project = self._project_repository.get_by_id(project_id)
        if project is None:
            raise ProjectNotFoundError("Project not found")
        dependency_run = self._dependency_repository.get_by_id(run.dependency_run_id)
        if dependency_run is None or dependency_run.status != "completed":
            raise DependencyRunNotReadyError(
                "Dependency run must be completed before test quality optimization"
            )
        source_directory = self._resolve_source_directory(
            project_id, project.storage_path
        )
        context = self._build_context(
            project_id=project_id,
            dependency_run_id=run.dependency_run_id,
            source_directory=source_directory,
            discovered_files=dependency_run.files,
        )
        return [item.model_dump(mode="json") for item in context.files]

    def _load_stage3_artifact(
        self,
        project_id: uuid.UUID,
        run_id: uuid.UUID,
    ) -> tuple[dict, CodeUnderstandingRun]:
        run = self._code_understanding_repository.get_by_id(run_id)
        if run is None:
            raise CodeUnderstandingRunNotFoundError("Code-understanding run not found")
        if run.project_id != project_id:
            raise CodeUnderstandingRunNotReadyError(
                "Code-understanding run does not belong to the requested project"
            )
        if run.status != "completed" or run.result is None:
            raise CodeUnderstandingRunNotReadyError(
                "Code-understanding run must be completed"
            )
        payload = dict(run.result)
        payload.pop("test_generation", None)
        payload.pop("test_verification", None)
        payload.pop("quality_evaluation", None)
        payload.pop("quality_optimization", None)
        return payload, run

    def get_run(
        self,
        run_id: uuid.UUID,
    ) -> CodeUnderstandingRun | None:
        return self._code_understanding_repository.get_by_id(run_id)

    def get_latest_run(
        self,
        project_id: uuid.UUID,
    ) -> CodeUnderstandingRun | None:
        return self._code_understanding_repository.get_latest_completed_by_project_id(
            project_id
        )

    def get_latest_workflow_run(
        self,
        project_id: uuid.UUID,
    ) -> CodeUnderstandingRun | None:
        """Return the latest Stage 3 attempt for approval-state inspection."""
        return self._code_understanding_repository.get_latest_by_project_id(project_id)

    def get_latest_pipeline_state(self, project_id: uuid.UUID) -> dict:
        if self._project_repository.get_by_id(project_id) is None:
            raise ProjectNotFoundError("Project not found")

        dependency_run = (
            self._dependency_repository.get_latest_completed_by_project_id(project_id)
        )
        understanding_run = (
            self._code_understanding_repository.get_latest_by_project_id(project_id)
        )
        security_repository = getattr(self, "_security_scan_repository", None)
        security_scan_run = (
            security_repository.get_latest_by_project_id(project_id)
            if security_repository is not None
            else None
        )
        publishable = bool(
            understanding_run is not None
            and understanding_run.status == CodeUnderstandingStatus.COMPLETED
            and self._artifact_version_matches(
                understanding_run,
                self._artifact_version_manifest(include_pipeline=True),
            )
        )
        result = (
            dict(understanding_run.result or {}) if publishable else {}
        )
        if understanding_run is not None and not publishable:
            logger.warning(
                "Suppressing partial or stale pipeline artifacts project_id=%s "
                "run_id=%s status=%s",
                project_id,
                understanding_run.id,
                understanding_run.status,
            )
        return {
            "project_id": project_id,
            "dependency_run": dependency_run,
            "security_scan_run": security_scan_run,
            "understanding_run": understanding_run,
            "artifacts_publishable": publishable,
            "test_generation": result.get("test_generation"),
            "test_verification": result.get("test_verification"),
            "quality_optimization": result.get("quality_optimization"),
            "runtime_execution_plan": result.get("runtime_execution_plan"),
        }

    def _resolve_source_directory(
        self,
        project_id: uuid.UUID,
        stored_path: str,
    ) -> Path:
        try:
            project_directory = self._storage_service.resolve_project_directory(
                project_id,
                stored_path,
            )
        except ValueError as error:
            raise InvalidSourcePathError(str(error)) from error

        source_directory = (project_directory / "source").resolve()
        if not source_directory.is_dir():
            raise InvalidSourcePathError("Project source directory does not exist")
        return source_directory

    def _load_cached_run(self, cached: object) -> CodeUnderstandingRun | None:
        """Resolve a valid cached artifact to its authoritative database run."""
        if not isinstance(cached, dict) or not isinstance(cached.get("run_id"), str):
            return None
        try:
            run_id = uuid.UUID(cached["run_id"])
        except ValueError:
            return None
        run = self._code_understanding_repository.get_by_id(run_id)
        if run is None or run.status != "completed" or run.result is None:
            return None
        return run

    def _source_content_hash(
        self,
        project_id: uuid.UUID,
        source_directory: Path,
        discovered_files: list,
    ) -> str:
        """Hash discovered source paths and complete file bytes deterministically."""
        digest = hashlib.sha256()
        # Version the content key when the provider contract/enrichment changes
        # so Redis cannot serve artifacts produced by an older Stage 3 schema.
        digest.update(b"code-understanding-content-v2-semantic-only\0")
        for discovered_file in sorted(discovered_files, key=lambda item: item.path):
            try:
                file_path = self._storage_service.resolve_project_path(
                    project_id, discovered_file.path
                )
            except ValueError as error:
                raise InvalidSourcePathError(str(error)) from error
            if not file_path.is_relative_to(source_directory) or not file_path.is_file():
                raise InvalidSourcePathError(
                    "Discovered file is missing or outside managed project storage"
                )
            relative_path = file_path.relative_to(source_directory).as_posix()
            digest.update(relative_path.encode("utf-8"))
            digest.update(b"\0")
            with file_path.open("rb") as source_file:
                for chunk in iter(lambda: source_file.read(64 * 1024), b""):
                    digest.update(chunk)
            digest.update(b"\0")
        return digest.hexdigest()

    def _build_context(
        self,
        project_id: uuid.UUID,
        dependency_run_id: uuid.UUID,
        source_directory: Path,
        discovered_files: list,
    ) -> CodeUnderstandingContext:
        files: list[SourceFileContext] = []
        omitted_files: list[str] = []
        for discovered_file in sorted(
            discovered_files,
            key=lambda item: item.path,
        ):
            try:
                file_path = self._storage_service.resolve_project_path(
                    project_id,
                    discovered_file.path,
                )
            except ValueError as error:
                raise InvalidSourcePathError(str(error)) from error
            if not file_path.is_relative_to(source_directory):
                raise InvalidSourcePathError(
                    "Discovered file is outside managed project storage"
                )
            relative_path = file_path.relative_to(source_directory).as_posix()
            if not file_path.is_file():
                raise InvalidSourcePathError(
                    f"Discovered file does not exist: {relative_path}"
                )
            # Stage 3A parses complete Python modules. Prompt-era character
            # limits are intentionally not applied to deterministic analysis.
            content = file_path.read_text(encoding="utf-8", errors="replace")

            files.append(
                SourceFileContext(
                    path=relative_path,
                    language=discovered_file.language,
                    is_entry_point=discovered_file.is_entry_point,
                    imports=discovered_file.imports or [],
                    classes=discovered_file.classes or [],
                    functions=discovered_file.functions or [],
                    content=content,
                    content_truncated=False,
                )
            )

        security_findings = []
        security_repository = getattr(self, "_security_scan_repository", None)
        security_run = (
            security_repository.get_latest_by_project_id(project_id)
            if security_repository is not None else None
        )
        if security_run is not None and security_run.status == "completed":
            security_findings = [
                {
                    "id": str(item.id),
                    "rule_id": item.rule_id,
                    "severity": item.severity,
                    "file": item.file,
                    "line": item.line,
                    "message": item.message,
                    "cwe": list(item.cwe or []),
                    "owasp": list(item.owasp or []),
                    "metadata": dict(item.semgrep_metadata or {}),
                }
                for item in security_run.findings
            ]

        return CodeUnderstandingContext(
            project_id=project_id,
            dependency_run_id=dependency_run_id,
            files=files,
            omitted_files=omitted_files,
            security_findings=security_findings,
        )

    @staticmethod
    def _read_bounded(file_path: Path, character_limit: int) -> str:
        with file_path.open("r", encoding="utf-8", errors="replace") as source_file:
            return source_file.read(character_limit + 1)

    @staticmethod
    def _safe_error_message(error: Exception) -> str:
        message = str(error).strip()
        if isinstance(error, CodeUnderstandingError) and message:
            return message[:2_000]
        return "Code understanding failed"

    def _artifact_version_manifest(
        self, *, include_pipeline: bool
    ) -> dict[str, str]:
        """Return the active deterministic identity for Stage 3-6 artifacts."""
        del include_pipeline  # Component identity is stable across entry points.
        generation_agent = getattr(self, "_test_generation_agent", None)
        verification_agent = getattr(self, "_test_verification_agent", None)
        generation = (
            generation_agent.cache_fingerprint()
            if generation_agent is not None
            else {"enabled": False}
        )
        verification = (
            verification_agent.cache_fingerprint()
            if verification_agent is not None
            else {"enabled": False}
        )
        return artifact_version_manifest(
            semantic={
                "contract_version": SEMANTIC_CONTRACT_VERSION,
                "prompt_version": getattr(self, "_prompt_version", "unknown"),
                "model_name": getattr(self, "_model_name", "unknown"),
            },
            generator=generation,
            verification=verification,
        )

    @staticmethod
    def _artifact_version_matches(
        run: CodeUnderstandingRun, active: dict[str, str]
    ) -> bool:
        result = run.result if isinstance(run.result, dict) else {}
        return result.get(ARTIFACT_VERSION_KEY) == active

    def _invalidate_stale_artifacts(
        self,
        run: CodeUnderstandingRun,
        project_id: uuid.UUID,
        active: dict[str, str],
    ) -> None:
        persisted = (
            run.result.get(ARTIFACT_VERSION_KEY)
            if isinstance(run.result, dict)
            else None
        )
        logger.warning(
            "ARTIFACT VERSION MISMATCH project_id=%s run_id=%s "
            "persisted=%s active=%s",
            project_id,
            run.id,
            persisted,
            active,
        )
        logger.info(
            "CACHE INVALIDATED artifact=pipeline project_id=%s run_id=%s",
            project_id,
            run.id,
        )
        cache_manager = getattr(self, "_cache_manager", None)
        if cache_manager is not None:
            cache_manager.clear_project(str(project_id))
        self._code_understanding_repository.prepare_artifact_regeneration(run)
        logger.info(
            "REGENERATING artifact=pipeline project_id=%s run_id=%s",
            project_id,
            run.id,
        )

    def _safe_fail_run(
        self,
        run: CodeUnderstandingRun,
        error: Exception,
        *,
        failed_stage: str,
    ) -> None:
        """Best-effort FAILED transition that never masks the pipeline error."""
        try:
            self._code_understanding_repository.fail(
                run,
                self._safe_error_message(error),
                failed_stage=failed_stage,
            )
        except Exception:
            logger.exception(
                "Failed to persist pipeline failure locally run_id=%s stage=%s",
                getattr(run, "id", None),
                failed_stage,
            )
