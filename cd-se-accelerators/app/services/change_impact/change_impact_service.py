import json
import logging
import os
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

from app.db.database import SessionLocal
from app.db.models import ProjectSnapshot, FileSnapshot, Project
from app.models.change_impact_models import ChangeImpactRequest, ChangeImpactResponse, TraceabilityStep, RecommendedTestCase
from app.models.ir_models import FrameworkAgnosticIR
from app.models.test_case_models import TestCase
from app.services.change_impact.dependency_analyzer import DependencyAnalyzer
from app.services.change_impact.impact_analyzer import ImpactAnalyzer
from app.services.change_impact.test_selection_service import TestSelectionService
from app.services.change_impact.snapshot_service import SnapshotService
from app.services.change_impact.file_diff_service import FileDiffService

# Downstream pipeline services for IR regeneration fallback
from app.services.project_scanner.project_scanner_service import ProjectScannerService
from app.services.framework_detection.framework_detector_service import FrameworkDetectorService
from app.services.project_analyzer.project_analyzer_service import ProjectAnalyzerService
from app.services.ir_generator.ir_generator_service import IRGeneratorService
from app.utils.ir_cache import get_cached_ir

from app.db.repository import ProjectRepository
from app.services.test_execution.execution_service import TestExecutionService, find_run_dir

logger = logging.getLogger(__name__)

PERSISTENT_RUNS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "generated_tests",
    "runs"
)


class ChangeImpactService:
    """Orchestrates change impact analysis and smart test execution."""

    def __init__(self) -> None:
        self.project_repo = ProjectRepository()
        self.test_selection_service = TestSelectionService()
        self.execution_service = TestExecutionService()
        self.snapshot_service = SnapshotService()
        self.file_diff_service = FileDiffService()

    def _get_persistent_run_dir(self, pipeline_run_id: str) -> str:
        return os.path.join(PERSISTENT_RUNS_DIR, pipeline_run_id)

    def _load_ir(self, project_path: str, pipeline_run_id: str) -> FrameworkAgnosticIR:
        """Fetch cached/durable IR, or regenerate statically from code if missing."""
        # 1. Check persistent runs directory for ir.json
        run_dir = self._get_persistent_run_dir(pipeline_run_id)
        ir_file = os.path.join(run_dir, "ir.json")
        if os.path.exists(ir_file):
            try:
                with open(ir_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return FrameworkAgnosticIR.model_validate(data)
            except Exception as exc:
                logger.warning("Failed to load ir.json from persistent directory: %s", exc)

        # 2. Check in-memory cache
        cached = get_cached_ir(pipeline_run_id)
        if cached:
            return cached

        # 3. Fallback: Reconstruct IR statically (no LLM, purely deterministic AST/parser)
        logger.info("IR not cached. Reconstructing statically for run %s", pipeline_run_id)
        
        scanner = ProjectScannerService()
        detector = FrameworkDetectorService()
        analyzer = ProjectAnalyzerService()
        ir_gen = IRGeneratorService()

        # Step A: Scan project to get index
        proj_idx = scanner.scan_project(project_path, "reconstructed", pipeline_run_id)
        
        # Step B: Detect framework
        fw_res = detector.detect(project_path)
        framework = fw_res.get("framework", "React")
        
        # Step C: Analyze project code (Babel/AST parser)
        analysis = analyzer.analyze(project_path, project_index=proj_idx)
        
        # Step D: Map to framework-agnostic IR
        analysis_dict = analysis.model_dump() if hasattr(analysis, "model_dump") else analysis
        analysis_dict["project_id"] = self.project_repo.resolve_project_id(pipeline_run_id)
        analysis_dict["pipeline_run_id"] = pipeline_run_id
        analysis_dict["framework"] = framework

        ir = ir_gen.generate_ir(analysis_dict)
        ir.project_id = analysis_dict["project_id"]
        ir.pipeline_run_id = pipeline_run_id

        # Cache the reconstructed IR durably
        try:
            os.makedirs(run_dir, exist_ok=True)
            with open(ir_file, "w", encoding="utf-8") as f:
                json.dump(ir.model_dump(), f, indent=2)
        except Exception as exc:
            logger.warning("Could not persist reconstructed ir.json: %s", exc)

        return ir

    def _load_test_cases_and_manifest(self, pipeline_run_id: str, project_path: str) -> Tuple[List[TestCase], Dict[str, Any]]:
        """Retrieve test cases and test manifest from disk or database fallbacks."""
        # A. Resolve run directories
        src_proj_path, run_dir = None, None
        try:
            src_proj_path, run_dir = find_run_dir(pipeline_run_id)
        except Exception:
            pass

        run_dirs = [self._get_persistent_run_dir(pipeline_run_id)]
        if run_dir:
            run_dirs.append(run_dir)
            run_dirs.append(os.path.dirname(run_dir))

        # 1. Load Test Case Plan
        test_cases: List[TestCase] = []
        plan_loaded = False
        
        for r_dir in run_dirs:
            plan_file = os.path.join(r_dir, "test_case_plan.json")
            if os.path.exists(plan_file):
                try:
                    with open(plan_file, "r", encoding="utf-8") as f:
                        plan_data = json.load(f)
                    for tc_dict in plan_data.get("test_cases", []):
                        test_cases.append(TestCase.model_validate(tc_dict))
                    plan_loaded = True
                    break
                except Exception as exc:
                    logger.warning("Failed loading plan from %s: %s", plan_file, exc)

        # Fallback to DB Test Cases
        if not plan_loaded:
            logger.info("Falling back to database for test cases retrieval")
            db_cases = self.project_repo.get_test_cases_by_project(pipeline_run_id, pipeline_run_id)
            for tc in db_cases:
                # Convert DB model to TestCase schema
                steps = tc.steps or []
                test_cases.append(TestCase(
                    id=tc.id,
                    strategy_id=tc.id.split("-")[1] if len(tc.id.split("-")) > 1 else "STRAT",
                    edge_case_id=tc.id.split("-")[2] if len(tc.id.split("-")) > 2 else "EC",
                    category=tc.category or "General",
                    priority=tc.priority or "Medium",
                    component=tc.component_rel.name if tc.component_rel else "Component",
                    title=tc.title,
                    objective=tc.objective or "",
                    expected_result=tc.expected_result or "",
                    metadata={
                        "component": tc.component_rel.name if tc.component_rel else "Component",
                        "element": "element",
                        "element_type": "element",
                        "locator": {"strategy": "id", "value": "element-id"},
                        "action": "click",
                        "assertion_type": "exists",
                        "assertion_target": "target"
                    }
                ))

        # 2. Load Manifest
        manifest = {}
        manifest_loaded = False
        
        for r_dir in run_dirs:
            manifest_file = os.path.join(r_dir, "test_manifest.json")
            if os.path.exists(manifest_file):
                try:
                    with open(manifest_file, "r", encoding="utf-8") as f:
                        manifest = json.load(f)
                    manifest_loaded = True
                    break
                except Exception as exc:
                    logger.warning("Failed loading manifest from %s: %s", manifest_file, exc)

        # Fallback to DB Test Files
        if not manifest_loaded:
            logger.info("Falling back to database for test manifest retrieval")
            db_files = self.project_repo.get_test_files_by_project(pipeline_run_id, pipeline_run_id)
            gen_files = []
            for tf in db_files:
                gen_files.append({
                    "component": tf.component_rel.name if tf.component_rel else tf.file_name.split(".")[0],
                    "file_name": tf.file_name,
                    "file": tf.file_name,
                    "file_path": tf.file_path,
                    "test_cases": tf.test_case_ids or []
                })
            manifest = {
                "pipeline_run_id": pipeline_run_id,
                "framework": "React",
                "generated_files": gen_files
            }

        return test_cases, manifest

    def analyze_impact(self, request: ChangeImpactRequest) -> ChangeImpactResponse:
        """Run change impact smart selection analysis, automatically diffing snapshots if needed."""
        logger.info("Starting change impact analysis for run %s", request.pipeline_run_id)
        
        session = SessionLocal()
        try:
            # 1. Resolve project stable identity
            project_id = request.project_id
            if not project_id:
                project_id = self.project_repo.resolve_project_id(request.pipeline_run_id)
            
            project = session.query(Project).filter(Project.id == project_id).first()
            project_path = request.project_path or (project.project_path if project else None)
            
            if not project_path or not os.path.exists(project_path):
                raise FileNotFoundError(f"Project directory path '{project_path}' does not exist on disk.")

            # 2. Load framework-agnostic IR
            ir = self._load_ir(project_path, request.pipeline_run_id)

            # 3. Handle snapshot retrieval
            current_snapshot = session.query(ProjectSnapshot).filter(
                ProjectSnapshot.pipeline_run_id == request.pipeline_run_id
            ).first()
            if not current_snapshot:
                current_snapshot = self.snapshot_service.create_snapshot(
                    project_id=project_id,
                    pipeline_run_id=request.pipeline_run_id,
                    workspace_path=project_path,
                    framework=ir.framework
                )

            previous_snapshot = self.snapshot_service.get_previous_snapshot(project_id, current_snapshot.id)

            # Load test suites
            test_cases, manifest = self._load_test_cases_and_manifest(request.pipeline_run_id, project_path)

            first_upload = (previous_snapshot is None)
            
            added_files = []
            modified_files = []
            deleted_files = []
            unchanged_files = [f.file_path for f in current_snapshot.file_snapshots]

            if first_upload:
                logger.info("Baseline project version detected for project %s. No change diff required.", project_id)
                
                response = ChangeImpactResponse(
                    total_tests=len(test_cases),
                    impacted_tests=0,
                    unaffected_tests=len(test_cases),
                    recommended_tests_count=0,
                    recommended_tests=[],
                    impact_score=0.0,
                    impact_level="LOW",
                    reasons=["This is the first version of this project. A baseline snapshot has been created."],
                    estimated_reduction_percent=100.0,
                    traceability=[],
                    project_id=project_id,
                    current_snapshot_id=current_snapshot.id,
                    change_summary={
                        "added": len(current_snapshot.file_snapshots),
                        "modified": 0,
                        "deleted": 0,
                        "unchanged": 0
                    },
                    first_upload=True,
                    deleted_components_traceability=[]
                )
            else:
                # Perform automatic diff
                diff = self.file_diff_service.diff_snapshots(previous_snapshot, current_snapshot)
                added_files = diff["added_files"]
                modified_files = diff["modified_files"]
                deleted_files = diff["deleted_files"]
                unchanged_files = diff["unchanged_files"]

                # Use manually input changed files if explicitly overridden in Request (backward-compatible)
                effective_changed_files = request.changed_files
                if effective_changed_files is None:
                    effective_changed_files = modified_files + added_files + deleted_files

                # 4. Build dependency maps and run traversal
                dep_analyzer = DependencyAnalyzer(ir)
                impact_analyzer = ImpactAnalyzer(dep_analyzer)
                
                impacted_components, impact_reasons, global_reasons = impact_analyzer.analyze_changed_files(effective_changed_files)
                
                # Check for added files/new components that might need generation
                for add_f in added_files:
                    comp_name = os.path.basename(add_f).split(".")[0]
                    # If this is a component file and not currently tested
                    if any(c.name == comp_name for c in ir.components):
                        if not any(tc.component == comp_name for tc in test_cases):
                            global_reasons.append(f"New component '{comp_name}' detected — tests recommended.")

                # Check for deleted files/traceability
                deleted_components_traceability = []
                for del_f in deleted_files:
                    comp_name = os.path.basename(del_f).split(".")[0]
                    for tc in test_cases:
                        if tc.component == comp_name:
                            test_file = f"tests/react/{comp_name}.test.jsx"
                            trace_step = TraceabilityStep(
                                changed_file=del_f,
                                component=comp_name,
                                ir_element=tc.target_function or "Component Render",
                                strategy=tc.strategy_id,
                                edge_case=tc.edge_case_id,
                                test_case_id=tc.id,
                                test_file=test_file
                            )
                            deleted_components_traceability.append(trace_step)
                            global_reasons.append(f"Component '{comp_name}' was deleted. Related test case '{tc.id}' is marked as obsolete.")

                # Run Selection logic
                response = self.test_selection_service.select_tests(
                    test_cases=test_cases,
                    manifest=manifest,
                    impacted_components=impacted_components,
                    impact_reasons=impact_reasons,
                    global_reasons=global_reasons,
                    changed_files=effective_changed_files
                )

                # Set new fields
                response.project_id = project_id
                response.previous_snapshot_id = previous_snapshot.id
                response.current_snapshot_id = current_snapshot.id
                response.change_summary = {
                    "added": len(added_files),
                    "modified": len(modified_files),
                    "deleted": len(deleted_files),
                    "unchanged": len(unchanged_files)
                }
                response.first_upload = False
                response.deleted_components_traceability = deleted_components_traceability

            # 5. Cache/persist analysis report durably in runs directory
            run_dir = self._get_persistent_run_dir(request.pipeline_run_id)
            os.makedirs(run_dir, exist_ok=True)
            try:
                with open(os.path.join(run_dir, "change_impact_analysis.json"), "w", encoding="utf-8") as f:
                    json.dump(response.model_dump(), f, indent=2)
            except Exception as exc:
                logger.warning("Could not persist change_impact_analysis.json: %s", exc)

            return response

        finally:
            session.close()
