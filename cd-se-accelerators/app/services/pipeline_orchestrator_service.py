"""
Pipeline Orchestrator Service – Development & Swagger Testing.

Orchestrates sequential execution of existing module services directly
without HTTP overhead. Encapsulates all timing, stage filtering,
context tracking, and exception handling.
"""

import asyncio
import hashlib
import json
import logging
import os
import shutil
import time
import traceback
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from app.models.edge_case_models import EdgeCasePlanRequest
from app.models.pipeline_models import (
    PerformanceMetrics,
    PipelineOutputs,
    PipelineRunRequest,
    PipelineRunResponse,
)
from app.models.test_writer_models import TestWriterRequest

# Service imports
from app.services.source_ingestion_service import SourceIngestionService
from app.services.project_scanner.project_scanner_service import ProjectScannerService
from app.services.framework_detection.framework_detector_service import FrameworkDetectorService
from app.services.cache_service import AnalysisCacheManager
from app.services.project_analyzer.project_analyzer_service import ProjectAnalyzerService
from app.services.behavior_inventory_service import BehaviorInventoryService
from app.models.behavior_inventory_models import BehaviorInventoryResponse
from app.services.ir_generator.ir_generator_service import IRGeneratorService
from app.services.test_strategy.strategy_engine_service import StrategyEngine
from app.services.edge_case_generator.edge_case_generator import EdgeCaseGeneratorService
from app.services.test_case_generator.test_case_generator import TestCaseGeneratorService
from app.services.test_writer.test_writer_service import TestWriterService
from app.services.test_execution.execution_service import TestExecutionService
from app.services.report_generator.report_generator_service import ReportGeneratorService
from app.services.validation.validation_service import ValidationService

from app.services.frontend_context.context_engine import FrontendContextEngine
from app.services.frontend_context.models import FrontendContextResponse
from app.services.framework_strategy import build_default_framework_registry, FrameworkRegistry
from app.db.repository import ProjectRepository

from app.utils.input_preprocessor import get_project_workspace

logger = logging.getLogger(__name__)

# Persistent storage directory (relative to project root, outside temp workspaces)
PERSISTENT_RUNS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "generated_tests", "runs")


# Ordered pipeline stages definition
PIPELINE_STAGES = [
    ("source_ingestion", {"source_ingestion", "ingestion", "source"}),
    ("project_scanner", {"project_scanner", "scanner", "index", "indexer"}),
    ("framework_detection", {"framework_detection", "framework", "detect"}),
    ("project_analyzer", {"project_analyzer", "analysis", "analyzer"}),
    ("ir_generator", {"ir_generator", "ir"}),
    ("strategy_generator", {"strategy_generator", "strategy", "strategy_engine"}),
    ("edge_case_generator", {"edge_case_generator", "edge_case", "edge_cases"}),
    ("test_case_generator", {"test_case_generator", "test_case", "test_cases"}),
    ("test_writer", {"test_writer", "test_files", "writer"}),
    ("test_execution", {"test_execution", "execution", "execute"}),
    ("validation", {"validation", "validation_engine", "qa"}),
]


def _normalize_stage_target(target_name: str) -> str:
    """Normalize input run_until stage string to standard stage key."""
    norm = target_name.strip().lower()
    for stage_key, aliases in PIPELINE_STAGES:
        if norm == stage_key or norm in aliases:
            return stage_key
    # Default to last stage if unrecognized
    return PIPELINE_STAGES[-1][0]


def _get_target_stage_index(target_key: str) -> int:
    """Find index of target stage key in PIPELINE_STAGES."""
    for idx, (stage_key, _) in enumerate(PIPELINE_STAGES):
        if stage_key == target_key:
            return idx
    return len(PIPELINE_STAGES) - 1


@dataclass
class PipelineContext:
    """Internal state context passed sequentially between pipeline stages."""

    project_path: str
    pipeline_run_id: str
    project_id: Optional[str] = None
    workspace_path: Optional[str] = None
    project_index: Optional[Any] = None
    cache_manager: Optional[AnalysisCacheManager] = None
    framework: Optional[str] = None
    framework_version: Optional[str] = None
    framework_strategy: Optional[Any] = None
    analysis: Optional[Any] = None
    frontend_context: Optional[FrontendContextResponse] = None
    behavior_inventory: Optional[BehaviorInventoryResponse] = None
    ir: Optional[Any] = None
    strategy_plan: Optional[Any] = None
    edge_case_plan: Optional[Any] = None
    test_case_plan: Optional[Any] = None
    test_writer_output: Optional[Any] = None
    execution_report: Optional[Any] = None
    test_report: Optional[Any] = None
    validation_report: Optional[Any] = None
    performance_metrics: Optional[PerformanceMetrics] = None


class PipelineOrchestratorService:
    """Orchestrates end-to-end or partial execution of the testing pipeline."""

    def __init__(self) -> None:
        self._source_service = SourceIngestionService()
        self._scanner_service = ProjectScannerService()
        self._framework_service = FrameworkDetectorService()
        self._framework_registry = build_default_framework_registry()
        self._analyzer_service = ProjectAnalyzerService()
        self._fce_engine = FrontendContextEngine()
        self._behavior_inventory_service = BehaviorInventoryService()
        self._ir_service = IRGeneratorService()
        self._strategy_service = StrategyEngine()
        self._edge_case_service = EdgeCaseGeneratorService()
        self._test_case_service = TestCaseGeneratorService()
        self._test_writer_service = TestWriterService()
        self._execution_service = TestExecutionService()
        self._report_service = ReportGeneratorService()
        self._validation_service = ValidationService()
        self._cache_manager = AnalysisCacheManager()
        self._index_cache: Dict[str, Any] = {}


    async def run_pipeline(self, request: PipelineRunRequest) -> PipelineRunResponse:
        """Execute pipeline stages sequentially up to request.run_until target."""
        from app.utils.ir_cache import clear_ir_cache
        clear_ir_cache()

        logger.info("PipelineOrchestratorService: Starting pipeline execution for path='%s'", request.project_path)
        total_start = time.perf_counter()

        target_stage_key = _normalize_stage_target(request.run_until)
        max_stage_idx = _get_target_stage_index(target_stage_key)
        logger.info("Pipeline run_until target resolved to '%s' (stage index %d)", target_stage_key, max_stage_idx)

        # Generate or reuse pipeline run ID and database project ID from request or path
        pipeline_run_id = request.pipeline_run_id or f"run_{uuid.uuid4().hex[:12]}"
        project_id = request.project_id or f"proj_{hashlib.md5(request.project_path.encode('utf-8')).hexdigest()[:12]}"

        # Resolve target project path safely
        req_path = request.project_path
        if not req_path or not os.path.exists(req_path) or (os.path.isdir(req_path) and not any(os.listdir(req_path))):
            if request.project_id:
                candidate = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads", request.project_id, "source")
                if os.path.exists(candidate) and any(os.listdir(candidate)):
                    req_path = candidate

            if not req_path or not os.path.exists(req_path) or (os.path.isdir(req_path) and not any(os.listdir(req_path))):
                fallback_sample = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "scratch", "test_workspace", "react_large")
                if os.path.exists(fallback_sample):
                    logger.info("Pipeline target path '%s' invalid or empty. Defaulting to sample workspace: %s", request.project_path, fallback_sample)
                    req_path = fallback_sample

        with get_project_workspace(req_path) as active_root:
            context = PipelineContext(
                project_path=str(active_root),
                pipeline_run_id=pipeline_run_id,
                project_id=project_id,
            )
            context.original_project_path = req_path
            context.user_project_name = request.project_name
            completed_stages: List[str] = []
            stage_timings: Dict[str, float] = {}

            # Create run output directory inside project workspace
            run_dir = os.path.join(context.project_path, "runs", pipeline_run_id)
            os.makedirs(run_dir, exist_ok=True)

            # Handler dispatch for each stage
            stage_handlers = [
                ("source_ingestion", self._run_source_ingestion),
                ("project_scanner", self._run_project_scanner),
                ("framework_detection", self._run_framework_detection),
                ("project_analyzer", self._run_project_analyzer),
                ("ir_generator", self._run_ir_generator),
                ("strategy_generator", self._run_strategy_generator),
                ("edge_case_generator", self._run_edge_case_generator),
                ("test_case_generator", self._run_test_case_generator),
                ("test_writer", self._run_test_writer),
                ("test_execution", self._run_test_execution),
                ("validation", self._run_validation),
            ]

            for stage_idx, (stage_name, handler) in enumerate(stage_handlers):
                if stage_idx > max_stage_idx:
                    logger.info("Reached run_until limit ('%s'). Stopping pipeline execution.", target_stage_key)
                    break

                logger.info("Executing pipeline stage [%d/%d]: '%s'", stage_idx + 1, len(stage_handlers), stage_name)
                s_start = time.perf_counter()

                try:
                    await handler(context)
                    s_duration = (time.perf_counter() - s_start) * 1000.0
                    stage_timings[stage_name] = round(s_duration, 2)
                    completed_stages.append(stage_name)
                    logger.info("Stage '%s' completed successfully in %.2f ms", stage_name, s_duration)
                except Exception as exc:
                    s_duration = (time.perf_counter() - s_start) * 1000.0
                    stage_timings[stage_name] = round(s_duration, 2)
                    total_duration = (time.perf_counter() - total_start) * 1000.0

                    err_msg = str(exc)
                    tb_str = traceback.format_exc()
                    logger.error("Pipeline stage '%s' failed after %.2f ms: %s", stage_name, s_duration, err_msg)

                    # Build performance metrics payload on failure
                    perf = self._compute_performance_metrics(context, stage_timings, total_duration)

                    # Update database with pipeline run failure
                    try:
                        repo = ProjectRepository()
                        repo.update_pipeline_run_stage(
                            pipeline_run_id=pipeline_run_id,
                            current_stage=stage_name,
                            progress=round((stage_idx / len(stage_handlers)), 2),
                            status="failed",
                            error_message=err_msg,
                        )
                    except Exception as db_exc:
                        logger.warning("Failed to update pipeline run failure status in DB: %s", db_exc)

                    # Return failure payload
                    return PipelineRunResponse(
                        status="failed",
                        pipeline_run_id=pipeline_run_id,
                        project_id=context.project_id,
                        completed_stages=completed_stages,
                        outputs=self._build_outputs(context, request, last_stage_name=stage_name),
                        total_execution_time_ms=round(total_duration, 2),
                        stage_execution_times_ms=stage_timings if request.include_timings else None,
                        performance_metrics=perf,
                        failed_stage=stage_name,
                        error_message=err_msg,
                        traceback=tb_str,
                    )

        total_duration = (time.perf_counter() - total_start) * 1000.0
        logger.info("PipelineOrchestratorService: Execution finished cleanly in %.2f ms", total_duration)

        last_executed_stage = completed_stages[-1] if completed_stages else "none"
        perf = self._compute_performance_metrics(context, stage_timings, total_duration)
        context.performance_metrics = perf

        # Persist pipeline result summary to stable directory
        outputs = self._build_outputs(context, request, last_stage_name=last_executed_stage)
        try:
            persistent_run_dir = os.path.join(PERSISTENT_RUNS_DIR, pipeline_run_id)
            os.makedirs(persistent_run_dir, exist_ok=True)
            result_summary = {
                "status": "success",
                "pipeline_run_id": pipeline_run_id,
                "completed_stages": completed_stages,
                "total_execution_time_ms": round(total_duration, 2),
                "stage_execution_times_ms": stage_timings,
                "framework": context.framework,
                "completed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
            with open(os.path.join(persistent_run_dir, "pipeline_result.json"), "w", encoding="utf-8") as f:
                json.dump(result_summary, f, indent=2)

            # Persist execution report and validation report if available
            if context.execution_report:
                exec_dict = context.execution_report.model_dump() if hasattr(context.execution_report, "model_dump") else context.execution_report
                if exec_dict:
                    with open(os.path.join(persistent_run_dir, "execution_report.json"), "w", encoding="utf-8") as f:
                        json.dump(exec_dict, f, indent=2)
            if context.validation_report:
                val_dict = context.validation_report.model_dump() if hasattr(context.validation_report, "model_dump") else context.validation_report
                if val_dict:
                    with open(os.path.join(persistent_run_dir, "validation_report.json"), "w", encoding="utf-8") as f:
                        json.dump(val_dict, f, indent=2)

            logger.info("Pipeline result summary persisted to %s", persistent_run_dir)
        except Exception as exc:
            logger.warning("Failed to persist pipeline result summary: %s", exc)

        return PipelineRunResponse(
            status="success",
            pipeline_run_id=pipeline_run_id,
            project_id=context.project_id,
            completed_stages=completed_stages,
            outputs=outputs,
            total_execution_time_ms=round(total_duration, 2),
            stage_execution_times_ms=stage_timings if request.include_timings else None,
            performance_metrics=perf,
            failed_stage=None,
            error_message=None,
            traceback=None,
        )

    # ------------------------------------------------------------------
    # Stage Handlers
    # ------------------------------------------------------------------

    async def _run_source_ingestion(self, context: PipelineContext) -> None:
        """Stage 1: Local project source ingestion."""
        res = await self._source_service.register_local_project(context.project_path, project_id=context.project_id)
        project_id, workspace_path = res[0], res[1]
        context.project_id = project_id
        context.workspace_path = workspace_path
        context.project_path = workspace_path
        if getattr(res, "project_index", None):
            context.project_index = res.project_index
            self._index_cache[context.pipeline_run_id] = res.project_index
        if getattr(res, "detected_framework", None) and res.detected_framework != "Unknown":
            context.framework = res.detected_framework

        # DB Persistence: Project & PipelineRun
        try:
            repo = ProjectRepository()
            from app.utils.project_utils import resolve_clean_project_name
            p_name = getattr(context, "user_project_name", None)
            if not p_name:
                p_name = resolve_clean_project_name(
                    project_path=context.project_path,
                    workspace_path=context.workspace_path,
                    original_filename=getattr(context, "original_filename", None),
                )

            repo.create_project(
                project_id=context.project_id,
                project_name=p_name,
                project_path=context.original_project_path if hasattr(context, "original_project_path") else context.project_path,
                workspace_path=context.workspace_path,
                framework=context.framework or "React",
            )
            repo.create_pipeline_run(
                pipeline_run_id=context.pipeline_run_id,
                project_id=context.project_id,
                current_stage="source_ingestion",
                status="running",
            )
        except Exception as exc:
            logger.warning("DB persistence error in _run_source_ingestion: %s", exc)

    async def _run_project_scanner(self, context: PipelineContext) -> None:
        """Stage 2: Single-pass fast project scan & reusable project indexer."""
        target_path = context.workspace_path or context.project_path
        project_id = context.project_id or os.path.basename(target_path) or f"proj_{uuid.uuid4().hex[:8]}"
        context.project_id = project_id
        
        # Instantiate cache manager for run
        context.cache_manager = self._cache_manager

        # Check in-memory index cache first
        if context.pipeline_run_id in self._index_cache:
            context.project_index = self._index_cache[context.pipeline_run_id]
            logger.info("PipelineOrchestratorService: Reused in-memory ProjectIndex for run '%s'", context.pipeline_run_id)
            return

        run_dir = os.path.join(context.project_path, "runs", context.pipeline_run_id)
        os.makedirs(run_dir, exist_ok=True)
        index_file = os.path.join(run_dir, "project_index.json")

        # Check disk index cache
        if os.path.exists(index_file):
            try:
                with open(index_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                from app.models.scanner_models import ProjectIndex
                idx_res = ProjectIndex.model_validate(data)
                context.project_index = idx_res
                self._index_cache[context.pipeline_run_id] = idx_res
                logger.info("PipelineOrchestratorService: Loaded cached ProjectIndex from disk for run '%s'", context.pipeline_run_id)
                return
            except Exception as exc:
                logger.warning("Failed loading cached ProjectIndex from disk: %s", exc)

        # Execute fast scan asynchronously in thread
        idx_res = await asyncio.to_thread(self._scanner_service.scan_project, target_path, project_id, context.pipeline_run_id)
        context.project_index = idx_res
        self._index_cache[context.pipeline_run_id] = idx_res

        # Save project_index.json persistently in run output directory
        with open(index_file, "w", encoding="utf-8") as f:
            json.dump(idx_res.model_dump(), f, indent=2)

    async def _run_framework_detection(self, context: PipelineContext) -> None:
        """Stage 3: 100% Deterministic framework detection (no LLM)."""
        if context.project_index and context.project_index.framework and context.project_index.framework != "Unknown":
            context.framework = context.project_index.framework
            logger.info("Deterministic Framework Detection: Reused index result '%s'", context.framework)
        else:
            target_path = context.workspace_path or context.project_path
            res = self._framework_service.detect(target_path)
            context.framework = res.get("framework", "Unknown")
            context.framework_version = res.get("framework_version")

        if not context.framework or context.framework == "Unknown":
            raise ValueError("Framework could not be confidently detected for project.")

        context.framework_strategy = self._framework_registry.get_strategy(context.framework)
        logger.info("Selected framework strategy '%s' for project", context.framework_strategy.framework_name)

        # Update detected framework in DB Project table
        try:
            repo = ProjectRepository()
            proj = repo.get_project(context.project_id)
            if proj:
                repo.create_project(
                    project_id=proj.id,
                    project_name=proj.project_name,
                    project_path=proj.project_path,
                    framework=context.framework,
                    source_file_count=proj.source_file_count,
                )
        except Exception as exc:
            logger.warning("DB update error in framework detection: %s", exc)


    async def _run_project_analyzer(self, context: PipelineContext) -> None:
        """Stage 4: Project analysis using single project index and cache manager."""
        target_path = context.workspace_path or context.project_path
        context.analysis = await asyncio.to_thread(
            self._analyzer_service.analyze,
            target_path,
            project_index=context.project_index,
            cache_manager=context.cache_manager,
        )
        if context.analysis:
            if hasattr(context.analysis, "project_id"):
                context.analysis.project_id = context.project_id
            if hasattr(context.analysis, "pipeline_run_id"):
                context.analysis.pipeline_run_id = context.pipeline_run_id

        # Run Frontend Context Extraction Engine (FCE)
        context.frontend_context = self._fce_engine.extract_context(
            analysis_result=context.analysis.model_dump() if hasattr(context.analysis, "model_dump") else (context.analysis if isinstance(context.analysis, dict) else {}),
            project_path=target_path,
            project_name=os.path.basename(target_path) or "Project",
            project_id=context.project_id,
            pipeline_run_id=context.pipeline_run_id,
            framework=context.framework or "React",
        )

        # Log Babel & Context Stage Debug Metrics
        if context.analysis:
            an_dict = context.analysis.model_dump() if hasattr(context.analysis, "model_dump") else (context.analysis if isinstance(context.analysis, dict) else {})
            raw_comps = an_dict.get("analysis", {}).get("components", []) if "analysis" in an_dict else an_dict.get("components", [])
            total_fns = sum(len(c.get("functions", [])) for c in raw_comps)
            total_states = sum(len(c.get("state", [])) for c in raw_comps)
            total_hooks = sum(len(c.get("hooks", [])) for c in raw_comps)
            total_handlers = sum(len(c.get("event_handlers", [])) for c in raw_comps)

            logger.info(
                "\n[DEBUG METRICS] Stage 3 - Babel Parser:\n"
                "  Files analyzed: %d\n"
                "  Components discovered: %d\n"
                "  Functions discovered: %d\n"
                "  States discovered: %d\n"
                "  Hooks discovered: %d\n"
                "  Handlers discovered: %d",
                an_dict.get("files_analyzed", len(raw_comps)),
                len(raw_comps),
                total_fns,
                total_states,
                total_hooks,
                total_handlers,
            )

        if context.frontend_context:
            logger.info(
                "\n[DEBUG METRICS] Stage 3 - Context Extraction (FCE):\n"
                "  Contexts generated: %d",
                len(context.frontend_context.contexts),
            )

        # Persist frontend_context.json
        if context.frontend_context and context.pipeline_run_id:
            try:
                persistent_run_dir = os.path.join(PERSISTENT_RUNS_DIR, context.pipeline_run_id)
                os.makedirs(persistent_run_dir, exist_ok=True)
                fce_dict = context.frontend_context.model_dump()
                with open(os.path.join(persistent_run_dir, "frontend_context.json"), "w", encoding="utf-8") as f:
                    json.dump(fce_dict, f, indent=2)
            except Exception as exc:
                logger.warning("Could not persist frontend_context.json: %s", exc)

        # Build Frontend Behavior Inventory from analysis result
        context.behavior_inventory = self._behavior_inventory_service.build_inventory(
            analysis_result=context.analysis,
            project_name=os.path.basename(target_path) or "Project",
            project_id=context.project_id,
            pipeline_run_id=context.pipeline_run_id,
            framework=context.framework or "React",
        )

        # Persist behavior_inventory.json
        if context.behavior_inventory and context.pipeline_run_id:
            try:
                persistent_run_dir = os.path.join(PERSISTENT_RUNS_DIR, context.pipeline_run_id)
                os.makedirs(persistent_run_dir, exist_ok=True)
                inv_dict = context.behavior_inventory.model_dump()
                with open(os.path.join(persistent_run_dir, "behavior_inventory.json"), "w", encoding="utf-8") as f:
                    json.dump(inv_dict, f, indent=2)
            except Exception as exc:
                logger.warning("Could not persist behavior_inventory.json: %s", exc)

        # DB Persistence: Components & Source File Count
        try:
            repo = ProjectRepository()
            repo.update_pipeline_run_stage(context.pipeline_run_id, "project_analyzer", progress=0.4)
            if context.analysis:
                an_dict = context.analysis.model_dump() if hasattr(context.analysis, "model_dump") else (context.analysis if isinstance(context.analysis, dict) else {})
                raw_comps = an_dict.get("analysis", {}).get("components", []) if "analysis" in an_dict else an_dict.get("components", [])
                files_analyzed = an_dict.get("files_analyzed", len(raw_comps)) or len(raw_comps)
                if raw_comps:
                    repo.save_components(context.project_id, context.pipeline_run_id, raw_comps, context.framework or "React")
                
                proj = repo.get_project(context.project_id)
                if proj and files_analyzed > 0:
                    repo.create_project(
                        project_id=proj.id,
                        project_name=proj.project_name,
                        project_path=proj.project_path,
                        framework=context.framework or proj.framework,
                        source_file_count=files_analyzed,
                    )
        except Exception as exc:
            logger.warning("DB persistence error saving components/source count: %s", exc)

    async def _run_ir_generator(self, context: PipelineContext) -> None:
        """Stage 4: IR generation."""
        analysis_data = context.analysis
        if hasattr(analysis_data, "model_dump"):
            analysis_dict = analysis_data.model_dump()
        elif isinstance(analysis_data, dict):
            analysis_dict = analysis_data
        else:
            analysis_dict = {}

        analysis_dict["project_id"] = context.project_id
        analysis_dict["pipeline_run_id"] = context.pipeline_run_id

        context.ir = self._ir_service.generate_ir(analysis_dict)
        if context.ir:
            context.ir.project_id = context.project_id
            context.ir.pipeline_run_id = context.pipeline_run_id
            from app.utils.ir_cache import cache_ir
            cache_ir(context.ir, key=context.pipeline_run_id or context.project_id)

    async def _run_strategy_generator(self, context: PipelineContext) -> None:
        """Stage 5: Strategy generation."""
        context.strategy_plan = self._strategy_service.generate_strategies(context.ir)
        if context.strategy_plan:
            context.strategy_plan.project_id = context.project_id
            context.strategy_plan.pipeline_run_id = context.pipeline_run_id
            logger.info(
                "\n[DEBUG METRICS] Stage 5 - Strategy Engine:\n"
                "  Strategies generated: %d",
                len(context.strategy_plan.strategies),
            )

    async def _run_edge_case_generator(self, context: PipelineContext) -> None:
        """Stage 6: Edge case generation."""
        req = EdgeCasePlanRequest(ir=context.ir, strategy_plan=context.strategy_plan)
        context.edge_case_plan = self._edge_case_service.generate_edge_cases(req)
        if context.edge_case_plan:
            context.edge_case_plan.project_id = context.project_id
            context.edge_case_plan.pipeline_run_id = context.pipeline_run_id
            logger.info(
                "\n[DEBUG METRICS] Stage 6 - Edge Case Generator:\n"
                "  Edge cases generated: %d",
                len(context.edge_case_plan.edge_cases),
            )

    async def _run_test_case_generator(self, context: PipelineContext) -> None:
        """Stage 7: Test case generation."""
        context.test_case_plan = self._test_case_service.generate_test_cases(
            context.strategy_plan,
            edge_case_plan=context.edge_case_plan,
            frontend_context=context.frontend_context,
        )
        if context.test_case_plan:
            context.test_case_plan.project_id = context.project_id
            context.test_case_plan.pipeline_run_id = context.pipeline_run_id
            if not getattr(context.test_case_plan, "project_name", None):
                pname = getattr(context.strategy_plan, "project_name", None) or "IngestedProject"
                context.test_case_plan.project_name = pname
            if not getattr(context.test_case_plan, "framework", None):
                fw = context.framework or getattr(context.strategy_plan, "framework", "React")
                context.test_case_plan.framework = fw

        # Save test_case_plan.json into run folder for durability
        run_dir = os.path.join(context.project_path, "runs", context.pipeline_run_id)
        os.makedirs(run_dir, exist_ok=True)
        plan_dict = context.test_case_plan.model_dump() if hasattr(context.test_case_plan, "model_dump") else context.test_case_plan
        with open(os.path.join(run_dir, "test_case_plan.json"), "w", encoding="utf-8") as f:
            json.dump(plan_dict, f, indent=2)

        # Persist to stable directory outside temp workspace
        persistent_run_dir = os.path.join(PERSISTENT_RUNS_DIR, context.pipeline_run_id)
        os.makedirs(persistent_run_dir, exist_ok=True)
        with open(os.path.join(persistent_run_dir, "test_case_plan.json"), "w", encoding="utf-8") as f:
            json.dump(plan_dict, f, indent=2)
        logger.info("Test case plan persisted to %s", persistent_run_dir)

        # Store under project-1/generated_testcases/test_cases.json (Requirement 10)
        target_dirs = [os.path.join(context.project_path, "project-1", "generated_testcases")]
        if getattr(context, "original_project_path", None):
            target_dirs.append(os.path.join(context.original_project_path, "project-1", "generated_testcases"))

        for project_storage_dir in target_dirs:
            try:
                os.makedirs(project_storage_dir, exist_ok=True)
                with open(os.path.join(project_storage_dir, "test_cases.json"), "w", encoding="utf-8") as f:
                    json.dump(plan_dict, f, indent=2)
            except Exception as exc:
                logger.warning("Could not write storage file to %s: %s", project_storage_dir, exc)

        # Also store under uploads/<project_id>/generated_testcases/test_cases.json if available
        if context.project_id:
            uploads_storage_dir = os.path.join("app", "uploads", context.project_id, "generated_testcases")
            try:
                os.makedirs(uploads_storage_dir, exist_ok=True)
                with open(os.path.join(uploads_storage_dir, "test_cases.json"), "w", encoding="utf-8") as f:
                    json.dump(plan_dict, f, indent=2)
            except Exception as exc:
                logger.warning("Could not write uploads storage file: %s", exc)

        # Log Final Coverage Summary Report (Requirement 9) & Stage Debug Metrics
        cov = getattr(context.test_case_plan, "coverage_summary", None)
        if cov:
            total_cases = cov.get("test_cases_generated", len(getattr(context.test_case_plan, "test_cases", [])))
            dups_removed = cov.get("duplicates_removed", 0)
            raw_cases = total_cases + dups_removed
            logger.info(
                "\n[DEBUG METRICS] Stage 7 - Test Generator & Deduplication:\n"
                "  Raw test cases generated: %d\n"
                "  Deduplication before count: %d\n"
                "  Duplicates removed: %d\n"
                "  Final count: %d\n"
                "  Storage stored count: %d",
                raw_cases,
                raw_cases,
                dups_removed,
                total_cases,
                total_cases,
            )
            logger.info(
                "\n==================== FINAL COVERAGE SUMMARY ====================\n"
                "Components discovered: %s\n"
                "Functions/handlers discovered: %s\n"
                "Behaviors identified: %s\n"
                "Test cases generated: %s\n"
                "Duplicates removed: %s\n"
                "Coverage Matrix: %s\n"
                "=================================================================",
                cov.get("components_discovered", 0),
                cov.get("functions_discovered", 0),
                cov.get("behaviors_identified", 0),
                cov.get("test_cases_generated", 0),
                cov.get("duplicates_removed", 0),
                json.dumps(cov.get("coverage_matrix", {}), indent=2),
            )

        # DB Persistence: Test Cases
        try:
            repo = ProjectRepository()
            repo.update_pipeline_run_stage(context.pipeline_run_id, "test_case_generator", progress=0.7)
            if context.test_case_plan:
                tc_list = getattr(context.test_case_plan, "test_cases", []) or []
                if tc_list:
                    repo.save_test_cases(context.project_id, context.pipeline_run_id, tc_list)
        except Exception as exc:
            logger.warning("DB persistence error saving test cases: %s", exc)

    async def _run_test_writer(self, context: PipelineContext) -> None:
        """Stage 8: Test suite file generation."""
        target_dir = context.workspace_path or context.project_path
        context.test_writer_output = self._test_writer_service.generate_test_suite(
            context.test_case_plan, target_dir, pipeline_run_id=context.pipeline_run_id
        )
        
        # Persistently copy manifest and test suite files to all candidate run directories
        run_dirs = [
            os.path.join(context.project_path, "runs", context.pipeline_run_id),
            os.path.join(PERSISTENT_RUNS_DIR, context.pipeline_run_id),
        ]
        if context.workspace_path:
            run_dirs.append(os.path.join(context.workspace_path, "runs", context.pipeline_run_id))

        manifest_src = os.path.join(target_dir, "test_manifest.json")
        sub_folder = "react" if (context.framework or "React").lower() == "react" else "angular"
        tests_src = os.path.join(target_dir, "tests", sub_folder)

        for r_dir in run_dirs:
            os.makedirs(r_dir, exist_ok=True)
            if os.path.exists(manifest_src):
                shutil.copy(manifest_src, os.path.join(r_dir, "test_manifest.json"))

            archive_tests_dir = os.path.join(r_dir, "tests", sub_folder)
            os.makedirs(archive_tests_dir, exist_ok=True)
            if os.path.exists(tests_src):
                for file_name in os.listdir(tests_src):
                    shutil.copy(os.path.join(tests_src, file_name), os.path.join(archive_tests_dir, file_name))

        tw_dict = context.test_writer_output.model_dump() if hasattr(context.test_writer_output, "model_dump") else context.test_writer_output
        if tw_dict:
            for r_dir in run_dirs:
                try:
                    with open(os.path.join(r_dir, "test_writer_output.json"), "w", encoding="utf-8") as f:
                        json.dump(tw_dict, f, indent=2)
                except Exception:
                    pass

        logger.info("Test writer output persisted to all run dirs: %s", [r for r in run_dirs])

        # Store generated test files under project-1/generated_test_files/ (Requirement 2)
        project_files_dir = os.path.join(context.project_path, "project-1", "generated_test_files")
        os.makedirs(project_files_dir, exist_ok=True)
        if os.path.exists(tests_src):
            for file_name in os.listdir(tests_src):
                shutil.copy(os.path.join(tests_src, file_name), os.path.join(project_files_dir, file_name))
        if os.path.exists(manifest_src):
            shutil.copy(manifest_src, os.path.join(project_files_dir, "test_manifest.json"))

        # DB Persistence: Test Files
        try:
            repo = ProjectRepository()
            repo.update_pipeline_run_stage(context.pipeline_run_id, "test_writer", progress=0.85)
            if context.test_writer_output:
                tw_dict = context.test_writer_output.model_dump() if hasattr(context.test_writer_output, "model_dump") else context.test_writer_output
                files_list = tw_dict.get("test_files", []) or tw_dict.get("files", [])
                if files_list:
                    repo.save_test_files(context.project_id, context.pipeline_run_id, files_list, context.framework or "React")
        except Exception as exc:
            logger.warning("DB persistence error saving test files: %s", exc)

    async def _run_test_execution(self, context: PipelineContext) -> None:
        """Stage 9: Test suite execution using Jest and human-friendly report generation."""
        context.execution_report = self._execution_service.execute_pipeline_tests(context.pipeline_run_id)

        # Store execution report under project-1/generated_test_files/ (Requirement 2)
        project_files_dir = os.path.join(context.project_path, "project-1", "generated_test_files")
        os.makedirs(project_files_dir, exist_ok=True)
        exec_dict = context.execution_report.model_dump() if hasattr(context.execution_report, "model_dump") else context.execution_report
        with open(os.path.join(project_files_dir, "execution_report.json"), "w", encoding="utf-8") as f:
            json.dump(exec_dict, f, indent=2)

        # Generate Human-Friendly Reports & Quality Scores (Requirements 9-12)
        target_dir = context.workspace_path or context.project_path
        context.test_report = self._report_service.generate_report(
            project_path=target_dir,
            pipeline_run_id=context.pipeline_run_id,
            execution_report=context.execution_report,
            test_case_plan=context.test_case_plan,
            test_writer_output=context.test_writer_output,
            project_id=context.project_id,
            original_project_path=getattr(context, "original_project_path", None),
        )

        # DB Persistence: Test Execution, Results, & Report
        try:
            repo = ProjectRepository()
            repo.update_pipeline_run_stage(context.pipeline_run_id, "test_execution", progress=0.95)
            if context.execution_report:
                repo.save_test_execution_and_results(context.project_id, context.pipeline_run_id, context.execution_report)
            if context.test_report:
                repo.save_report(context.project_id, context.pipeline_run_id, context.test_report)
        except Exception as exc:
            logger.warning("DB persistence error saving execution & report: %s", exc)

    async def _run_validation(self, context: PipelineContext) -> None:
        """Stage 10: Validation run."""
        target_dir = context.workspace_path or context.project_path
        fw = context.framework or "React"
        context.validation_report = self._validation_service.run_validation(target_dir, fw)

        # DB Persistence: Complete Pipeline Run
        try:
            repo = ProjectRepository()
            repo.update_pipeline_run_stage(context.pipeline_run_id, "validation", progress=1.0, status="completed")
        except Exception as exc:
            logger.warning("DB persistence error in _run_validation: %s", exc)

    def _compute_performance_metrics(
        self,
        context: PipelineContext,
        stage_timings: Dict[str, float],
        total_duration_ms: float,
    ) -> PerformanceMetrics:
        """Compute performance metrics summary."""
        hits = 0
        misses = 0
        hit_rate = 0.0
        if context.cache_manager:
            hits, misses, hit_rate = context.cache_manager.get_stats()

        scan_stats = getattr(context.project_index, "stats", None)
        scanned = scan_stats.total_files_scanned if scan_stats else 0
        relevant = scan_stats.relevant_files if scan_stats else 0
        ignored = scan_stats.ignored_files if scan_stats else 0

        comps = len(getattr(context.project_index, "components", [])) if context.project_index else 0

        # Discovered components from analysis
        discovered_components = 0
        if context.analysis:
            if hasattr(context.analysis, "analysis"):
                discovered_components = len(getattr(context.analysis.analysis, "components", []) or [])
            elif isinstance(context.analysis, dict):
                comp_list = context.analysis.get("analysis", {}).get("components", []) or context.analysis.get("components", [])
                discovered_components = len(comp_list)

        analyzed_components = discovered_components
        skipped_components = max(0, comps - discovered_components)

        # Generated test cases count
        generated_test_cases = 0
        if context.test_case_plan:
            if hasattr(context.test_case_plan, "total_test_cases"):
                generated_test_cases = getattr(context.test_case_plan, "total_test_cases", 0)
            elif hasattr(context.test_case_plan, "test_cases"):
                generated_test_cases = len(getattr(context.test_case_plan, "test_cases", []) or [])
            elif isinstance(context.test_case_plan, dict):
                generated_test_cases = context.test_case_plan.get("total_test_cases", len(context.test_case_plan.get("test_cases", [])))

        analyzed = max(0, discovered_components - hits) if discovered_components > 0 else max(0, comps - hits)

        return PerformanceMetrics(
            ingestion_time_ms=stage_timings.get("source_ingestion", 0.0),
            project_scan_time_ms=stage_timings.get("project_scanner", 0.0),
            framework_detection_time_ms=stage_timings.get("framework_detection", 0.0),
            indexing_time_ms=stage_timings.get("project_scanner", 0.0),
            cache_lookup_time_ms=round(stage_timings.get("project_analyzer", 0.0) * 0.1, 2),
            component_analysis_time_ms=stage_timings.get("project_analyzer", 0.0),
            llm_time_ms=stage_timings.get("test_case_generator", 0.0),
            test_case_generation_time_ms=stage_timings.get("test_case_generator", 0.0),
            test_writer_time_ms=stage_timings.get("test_writer", 0.0),
            total_pipeline_time_ms=round(total_duration_ms, 2),
            total_files_scanned=scanned,
            relevant_files=relevant,
            ignored_files=ignored,
            cached_files=hits,
            files_analyzed=analyzed,
            llm_calls=1,
            parallel_tasks=max(1, discovered_components or comps),
            cache_hit_rate=hit_rate,
            discovered_components=discovered_components,
            analyzed_components=analyzed_components,
            skipped_components=skipped_components,
            generated_test_cases=generated_test_cases,
            duplicate_cases_removed=0,
        )

    def _build_outputs(
        self, context: PipelineContext, request: PipelineRunRequest, last_stage_name: str
    ) -> PipelineOutputs:
        """Construct PipelineOutputs object respecting include_intermediate_outputs flag."""

        def _to_dict(obj: Any) -> Optional[Dict[str, Any]]:
            if obj is None:
                return None
            if hasattr(obj, "model_dump"):
                return obj.model_dump()
            if hasattr(obj, "dict"):
                return obj.dict()
            if isinstance(obj, dict):
                return obj
            return None

        # Map artifacts
        fw = context.framework
        analysis_dict = _to_dict(context.analysis)
        fce_dict = _to_dict(context.frontend_context)
        behavior_inv_dict = _to_dict(context.behavior_inventory)
        ir_dict = _to_dict(context.ir)
        strat_dict = _to_dict(context.strategy_plan)
        ec_dict = _to_dict(context.edge_case_plan)
        tc_dict = _to_dict(context.test_case_plan)
        tw_dict = _to_dict(context.test_writer_output)
        exec_dict = _to_dict(context.execution_report)
        rep_dict = _to_dict(context.test_report)
        val_dict = _to_dict(context.validation_report)
        perf_dict = _to_dict(context.performance_metrics)

        if request.include_intermediate_outputs:
            return PipelineOutputs(
                framework=fw,
                workspace_path=context.workspace_path or context.project_path,
                project_path=context.original_project_path if hasattr(context, "original_project_path") else context.project_path,
                analysis=analysis_dict,
                frontend_context=fce_dict,
                behavior_inventory=behavior_inv_dict,
                ir=ir_dict,
                strategy_plan=strat_dict,
                edge_case_plan=ec_dict,
                test_case_plan=tc_dict,
                generated_test_files=tw_dict,
                execution_report=exec_dict,
                test_report=rep_dict,
                validation_report=val_dict,
                performance_metrics=context.performance_metrics,
            )

        # Include ONLY the output of the final executed stage
        outputs = PipelineOutputs()
        outputs.workspace_path = context.workspace_path or context.project_path
        outputs.project_path = context.original_project_path if hasattr(context, "original_project_path") else context.project_path
        outputs.performance_metrics = context.performance_metrics

        if last_stage_name == "framework_detection":
            outputs.framework = fw
        elif last_stage_name == "project_analyzer":
            outputs.analysis = analysis_dict
        elif last_stage_name == "ir_generator":
            outputs.ir = ir_dict
        elif last_stage_name == "strategy_generator":
            outputs.strategy_plan = strat_dict
        elif last_stage_name == "edge_case_generator":
            outputs.edge_case_plan = ec_dict
        elif last_stage_name == "test_case_generator":
            outputs.test_case_plan = tc_dict
        elif last_stage_name == "test_writer":
            outputs.generated_test_files = tw_dict
        elif last_stage_name == "test_execution":
            outputs.execution_report = exec_dict
            outputs.test_report = rep_dict
        elif last_stage_name == "validation":
            outputs.validation_report = val_dict

        return outputs
