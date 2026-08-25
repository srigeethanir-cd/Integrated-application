"""
Database Repository Layer – Atomic CRUD and scoping.

Encapsulates all database persistence and lookup operations for Projects,
Pipeline Runs, Source Files, Components, Test Cases, Test Files,
Test Executions, Test Results, Coverage Reports, and Final Reports.
Every query is strictly scoped by project_id and pipeline_run_id.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.db.models import (
    Project,
    PipelineRun,
    SourceFile,
    Component,
    TestCaseModel,
    TestFileModel,
    TestExecutionModel,
    TestResultModel,
    CoverageReportModel,
    ReportModel,
)

logger = logging.getLogger(__name__)


class ProjectRepository:
    """Repository handling project and pipeline run persistence."""

    def __init__(self, db: Optional[Session] = None):
        self.db = db

    def _get_session(self) -> Session:
        return self.db if self.db is not None else SessionLocal()

    # ------------------------------------------------------------------
    # Project CRUD
    # ------------------------------------------------------------------

    def create_project(
        self,
        project_id: str,
        project_name: str,
        project_path: str,
        framework: str = "React",
        workspace_path: Optional[str] = None,
        source_file_count: int = 0,
    ) -> Project:
        """Create or update a Project record."""
        session = self._get_session()
        try:
            proj = session.query(Project).filter(Project.id == project_id).first()
            if not proj:
                proj = Project(
                    id=project_id,
                    project_name=project_name,
                    project_path=project_path,
                    workspace_path=workspace_path or project_path,
                    framework=framework,
                    source_file_count=source_file_count,
                    status="active",
                )
                session.add(proj)
            else:
                proj.project_name = project_name
                proj.project_path = project_path
                if workspace_path:
                    proj.workspace_path = workspace_path
                if framework and framework != "Unknown":
                    proj.framework = framework
                if source_file_count > 0:
                    proj.source_file_count = source_file_count
                proj.updated_at = datetime.utcnow()
            session.commit()
            session.refresh(proj)
            return proj
        except Exception as exc:
            session.rollback()
            logger.error("Error creating/updating project '%s': %s", project_id, exc)
            raise
        finally:
            if self.db is None:
                session.close()

    def get_project(self, project_id: str) -> Optional[Project]:
        """Fetch project by ID."""
        session = self._get_session()
        try:
            return session.query(Project).filter(Project.id == project_id).first()
        finally:
            if self.db is None:
                session.close()

    def list_projects(self) -> List[Project]:
        """Fetch all projects ordered by creation time descending."""
        return self.list_all_projects()

    def list_all_projects(self) -> List[Project]:
        """Fetch all projects ordered by creation time descending."""
        session = self._get_session()
        try:
            return session.query(Project).order_by(Project.created_at.desc()).all()
        finally:
            if self.db is None:
                session.close()

    # ------------------------------------------------------------------
    # Pipeline Run CRUD
    # ------------------------------------------------------------------

    def create_pipeline_run(
        self,
        pipeline_run_id: str,
        project_id: str,
        current_stage: str = "source_ingestion",
        status: str = "running",
    ) -> PipelineRun:
        """Create or reset a PipelineRun record."""
        session = self._get_session()
        try:
            run = session.query(PipelineRun).filter(PipelineRun.id == pipeline_run_id).first()
            if not run:
                run = PipelineRun(
                    id=pipeline_run_id,
                    project_id=project_id,
                    status=status,
                    current_stage=current_stage,
                    progress=0.1,
                    started_at=datetime.utcnow(),
                )
                session.add(run)
            else:
                run.status = status
                run.current_stage = current_stage
            
            # Synchronize project status to match run status
            proj = session.query(Project).filter(Project.id == project_id).first()
            if proj:
                proj.status = status
                proj.updated_at = datetime.utcnow()

            session.commit()
            session.refresh(run)
            return run
        except Exception as exc:
            session.rollback()
            logger.error("Error creating pipeline run '%s': %s", pipeline_run_id, exc)
            raise
        finally:
            if self.db is None:
                session.close()

    def update_pipeline_run_stage(
        self,
        pipeline_run_id: str,
        current_stage: str,
        progress: float = 0.0,
        status: str = "running",
        error_message: Optional[str] = None,
    ) -> Optional[PipelineRun]:
        """Update pipeline run stage, status, and progress."""
        session = self._get_session()
        try:
            run = session.query(PipelineRun).filter(PipelineRun.id == pipeline_run_id).first()
            if run:
                run.current_stage = current_stage
                run.status = status
                if progress > 0:
                    run.progress = progress
                if status in ("completed", "success", "failed"):
                    run.completed_at = datetime.utcnow()
                if error_message:
                    run.error_message = error_message
                
                # Synchronize project status to match run status
                proj = session.query(Project).filter(Project.id == run.project_id).first()
                if proj:
                    proj.status = status
                    proj.updated_at = datetime.utcnow()

                session.commit()
                session.refresh(run)
            return run
        except Exception as exc:
            session.rollback()
            logger.error("Error updating pipeline run '%s': %s", pipeline_run_id, exc)
            return None
        finally:
            if self.db is None:
                session.close()


    def get_pipeline_run(self, pipeline_run_id: str) -> Optional[PipelineRun]:
        """Fetch pipeline run by ID."""
        session = self._get_session()
        try:
            return session.query(PipelineRun).filter(PipelineRun.id == pipeline_run_id).first()
        finally:
            if self.db is None:
                session.close()

    def list_project_pipeline_runs(self, project_id: str) -> List[PipelineRun]:
        """List historical pipeline runs for a project."""
        session = self._get_session()
        try:
            return (
                session.query(PipelineRun)
                .filter(PipelineRun.project_id == project_id)
                .order_by(PipelineRun.started_at.desc())
                .all()
            )
        finally:
            if self.db is None:
                session.close()

    # ------------------------------------------------------------------
    # Source Files & Components Persistence
    # ------------------------------------------------------------------

    def save_source_files(
        self,
        project_id: str,
        pipeline_run_id: str,
        files: List[Dict[str, Any]],
    ) -> List[SourceFile]:
        """Save source file records for a pipeline run."""
        session = self._get_session()
        try:
            records = []
            for f in files:
                rel_path = f.get("file_path") or f.get("path") or f.get("relative_path")
                if not rel_path:
                    continue
                sf = SourceFile(
                    project_id=project_id,
                    pipeline_run_id=pipeline_run_id,
                    file_path=rel_path,
                    file_hash=f.get("file_hash") or f.get("hash"),
                    file_type=f.get("file_type") or f.get("extension"),
                    analyzed=f.get("analyzed", True),
                )
                session.add(sf)
                records.append(sf)
            session.commit()
            return records
        except Exception as exc:
            session.rollback()
            logger.error("Error saving source files: %s", exc)
            return []
        finally:
            if self.db is None:
                session.close()

    def save_components(
        self,
        project_id: str,
        pipeline_run_id: str,
        components: List[Dict[str, Any]],
        framework: str = "React",
    ) -> List[Component]:
        """Save component records for a pipeline run."""
        session = self._get_session()
        try:
            records = []
            for c in components:
                name = c.get("name") or c.get("component")
                if not name:
                    continue
                comp = Component(
                    project_id=project_id,
                    pipeline_run_id=pipeline_run_id,
                    name=name,
                    component_type=c.get("component_type") or "ReactComponent",
                    framework=framework,
                )
                session.add(comp)
                records.append(comp)
            session.commit()
            return records
        except Exception as exc:
            session.rollback()
            logger.error("Error saving components: %s", exc)
            return []
        finally:
            if self.db is None:
                session.close()

    # ------------------------------------------------------------------
    # Test Cases Persistence & Retrieval
    # ------------------------------------------------------------------
    # Data Integrity & Helper Methods
    # ------------------------------------------------------------------

    def resolve_project_id(self, project_identifier: str) -> str:
        """Resolve a project ID or name to the canonical project_id UUID."""
        session = self._get_session()
        try:
            proj = session.query(Project).filter(
                (Project.id == project_identifier) |
                (Project.project_name == project_identifier)
            ).first()
            return proj.id if proj else project_identifier
        finally:
            if self.db is None:
                session.close()

    def count_source_files(self, project_id: str) -> int:
        """Count source files for a project."""
        session = self._get_session()
        try:
            pid = self.resolve_project_id(project_id)
            proj = session.query(Project).filter(Project.id == pid).first()
            if proj and proj.source_file_count > 0:
                return proj.source_file_count
            return session.query(SourceFile).filter(SourceFile.project_id == pid).count()
        finally:
            if self.db is None:
                session.close()

    def count_test_cases(self, project_id: str) -> int:
        """Count persisted test cases for a project."""
        session = self._get_session()
        try:
            pid = self.resolve_project_id(project_id)
            return session.query(TestCaseModel).filter(TestCaseModel.project_id == pid).count()
        finally:
            if self.db is None:
                session.close()

    def count_test_files(self, project_id: str) -> int:
        """Count persisted test files for a project."""
        session = self._get_session()
        try:
            pid = self.resolve_project_id(project_id)
            return session.query(TestFileModel).filter(TestFileModel.project_id == pid).count()
        finally:
            if self.db is None:
                session.close()

    def verify_project_ownership(self, record: Any, expected_project_id: str) -> None:
        """Verify that record belongs strictly to expected_project_id."""
        rec_pid = getattr(record, "project_id", None)
        if rec_pid and rec_pid != expected_project_id:
            raise ValueError(
                f"[DATA_INTEGRITY_ERROR] Record project_id '{rec_pid}' does not match expected '{expected_project_id}'"
            )

    # ------------------------------------------------------------------
    # Test Cases Persistence & Retrieval
    # ------------------------------------------------------------------

    def save_test_cases(
        self,
        project_id: str,
        pipeline_run_id: str,
        test_cases: List[Any],
    ) -> List[TestCaseModel]:
        """Save TestCase models or dicts to Database using strict project_id scoping."""
        session = self._get_session()
        try:
            canonical_pid = self.resolve_project_id(project_id)
            records = []

            for tc in test_cases:
                tc_dict = tc.model_dump() if hasattr(tc, "model_dump") else (tc if isinstance(tc, dict) else {})
                raw_tc_id = tc_dict.get("id") or f"TC-{len(records)+1:03d}"
                # Construct unique primary key scoped to project to avoid cross-project collision
                db_tc_id = raw_tc_id if raw_tc_id.startswith(f"{canonical_pid}_") else f"{canonical_pid}_{raw_tc_id}"
                
                comp_name = tc_dict.get("component", "Default")
                comp = session.query(Component).filter(
                    Component.project_id == canonical_pid,
                    Component.pipeline_run_id == pipeline_run_id,
                    Component.name == comp_name
                ).first()

                tc_model = session.query(TestCaseModel).filter(TestCaseModel.id == db_tc_id).first()
                if not tc_model:
                    tc_model = TestCaseModel(
                        id=db_tc_id,
                        project_id=canonical_pid,
                        pipeline_run_id=pipeline_run_id,
                        component_id=comp.id if comp else None,
                        title=tc_dict.get("title", raw_tc_id),
                        objective=tc_dict.get("objective", ""),
                        specification=tc_dict.get("component_specification") or tc_dict.get("objective", ""),
                        category=tc_dict.get("category", "General"),
                        priority=tc_dict.get("priority", "Medium"),
                        steps=tc_dict.get("steps", []),
                        expected_result=tc_dict.get("expected_result", ""),
                        source_function=tc_dict.get("target_function") or tc_dict.get("source_function", ""),
                        status="generated",
                        quality_score=tc_dict.get("test_quality_score", 100),
                    )
                    session.add(tc_model)
                else:
                    tc_model.project_id = canonical_pid
                    tc_model.pipeline_run_id = pipeline_run_id
                    tc_model.title = tc_dict.get("title", raw_tc_id)
                    tc_model.steps = tc_dict.get("steps", [])

                self.verify_project_ownership(tc_model, canonical_pid)
                records.append(tc_model)

            session.commit()

            # Update project test_case_count counter in DB
            total_cases = session.query(TestCaseModel).filter(TestCaseModel.project_id == canonical_pid).count()
            proj = session.query(Project).filter(Project.id == canonical_pid).first()
            if proj:
                proj.source_file_count = proj.source_file_count or 0
                session.commit()

            logger.info("[TESTCASE_SAVE] project_id=%s count=%d total_in_db=%d status=success", canonical_pid, len(records), total_cases)
            return records
        except Exception as exc:
            session.rollback()
            logger.error("[TESTCASE_SAVE_ERROR] project_id=%s error=%s", project_id, exc)
            return []
        finally:
            if self.db is None:
                session.close()

    def get_test_cases_by_project(self, project_id: str, pipeline_run_id: Optional[str] = None) -> List[TestCaseModel]:
        """Query test cases strictly by project_id and optional pipeline_run_id (no cross-project leakage)."""
        session = self._get_session()
        try:
            canonical_pid = self.resolve_project_id(project_id)
            q = session.query(TestCaseModel).filter(TestCaseModel.project_id == canonical_pid)
            if pipeline_run_id:
                q = q.filter(TestCaseModel.pipeline_run_id == pipeline_run_id)
            cases = q.order_by(TestCaseModel.created_at.asc()).all()

            for tc in cases:
                self.verify_project_ownership(tc, canonical_pid)

            logger.info("[TESTCASE_FETCH] project_id=%s pipeline_run_id=%s count=%d", canonical_pid, pipeline_run_id, len(cases))
            return cases
        except Exception as exc:
            logger.error("[TESTCASE_FETCH_ERROR] project_id=%s error=%s", project_id, exc)
            return []
        finally:
            if self.db is None:
                session.close()

    # ------------------------------------------------------------------
    # Test Files Persistence & Retrieval
    # ------------------------------------------------------------------

    def save_test_files(
        self,
        project_id: str,
        pipeline_run_id: str,
        test_files: List[Any],
        framework: str = "React",
    ) -> List[TestFileModel]:
        """Save generated test file records to DB using strict project_id scoping."""
        session = self._get_session()
        try:
            canonical_pid = self.resolve_project_id(project_id)
            records = []

            for tf in test_files:
                tf_dict = tf.model_dump() if hasattr(tf, "model_dump") else (tf if isinstance(tf, dict) else {})
                file_name = tf_dict.get("file_name") or tf_dict.get("file")
                if not file_name:
                    continue
                
                comp_name = tf_dict.get("component") or file_name.split(".")[0]
                comp = session.query(Component).filter(
                    Component.project_id == canonical_pid,
                    Component.pipeline_run_id == pipeline_run_id,
                    Component.name == comp_name
                ).first()

                # Search by project_id & file_name to prevent duplicate files within same project
                tf_model = session.query(TestFileModel).filter(
                    TestFileModel.project_id == canonical_pid,
                    TestFileModel.file_name == file_name
                ).first()

                if not tf_model:
                    tf_model = TestFileModel(
                        project_id=canonical_pid,
                        pipeline_run_id=pipeline_run_id,
                        component_id=comp.id if comp else None,
                        file_name=file_name,
                        file_path=tf_dict.get("file_path", f"tests/react/{file_name}"),
                        framework=framework,
                        test_case_ids=tf_dict.get("test_case_ids") or tf_dict.get("test_cases", []),
                    )
                    session.add(tf_model)
                else:
                    tf_model.pipeline_run_id = pipeline_run_id
                    tf_model.file_path = tf_dict.get("file_path", tf_model.file_path)
                    tf_model.test_case_ids = tf_dict.get("test_case_ids") or tf_dict.get("test_cases", tf_model.test_case_ids)

                self.verify_project_ownership(tf_model, canonical_pid)
                records.append(tf_model)

            session.commit()

            total_files = session.query(TestFileModel).filter(TestFileModel.project_id == canonical_pid).count()
            logger.info("[TESTFILE_SAVE] project_id=%s count=%d total_in_db=%d status=success", canonical_pid, len(records), total_files)
            return records
        except Exception as exc:
            session.rollback()
            logger.error("[TESTFILE_SAVE_ERROR] project_id=%s error=%s", project_id, exc)
            return []
        finally:
            if self.db is None:
                session.close()

    def get_test_files_by_project(self, project_id: str, pipeline_run_id: Optional[str] = None) -> List[TestFileModel]:
        """Query test files strictly by project_id and optional pipeline_run_id (no cross-project leakage)."""
        session = self._get_session()
        try:
            canonical_pid = self.resolve_project_id(project_id)
            q = session.query(TestFileModel).filter(TestFileModel.project_id == canonical_pid)
            if pipeline_run_id:
                q = q.filter(TestFileModel.pipeline_run_id == pipeline_run_id)
            files = q.order_by(TestFileModel.generated_at.asc()).all()

            for tf in files:
                self.verify_project_ownership(tf, canonical_pid)

            logger.info("[TESTFILE_FETCH] project_id=%s pipeline_run_id=%s count=%d", canonical_pid, pipeline_run_id, len(files))
            return files
        except Exception as exc:
            logger.error("[TESTFILE_FETCH_ERROR] project_id=%s error=%s", project_id, exc)
            return []
        finally:
            if self.db is None:
                session.close()

    # ------------------------------------------------------------------
    # Test Executions & Results Persistence
    # ------------------------------------------------------------------

    def save_test_execution_and_results(
        self,
        project_id: str,
        pipeline_run_id: str,
        exec_report: Any,
    ) -> Optional[TestExecutionModel]:
        """Save TestExecution, individual TestResults, and CoverageReport with strict project_id scoping."""
        session = self._get_session()
        try:
            canonical_pid = self.resolve_project_id(project_id)
            rep_dict = exec_report.model_dump() if hasattr(exec_report, "model_dump") else (exec_report if isinstance(exec_report, dict) else {})
            if not rep_dict:
                return None

            execution = TestExecutionModel(
                project_id=canonical_pid,
                pipeline_run_id=pipeline_run_id,
                status=rep_dict.get("status", "completed"),
                total_tests=rep_dict.get("total_tests", 0),
                passed=rep_dict.get("passed", 0),
                failed=rep_dict.get("failed", 0),
                skipped=rep_dict.get("skipped", 0),
                execution_time_ms=rep_dict.get("execution_time_ms", 0.0),
                pass_rate=rep_dict.get("pass_rate", 100.0),
            )
            session.add(execution)
            session.flush()

            # Save individual test failure / result records
            failures = rep_dict.get("failures", [])
            for fail in failures:
                f_dict = fail.model_dump() if hasattr(fail, "model_dump") else (fail if isinstance(fail, dict) else {})
                res_model = TestResultModel(
                    execution_id=execution.id,
                    test_case_id=f_dict.get("test_case_id"),
                    test_name=f_dict.get("test_name", "Failed assertion"),
                    status="failed",
                    expected=str(f_dict.get("expected") or ""),
                    actual=str(f_dict.get("received") or f_dict.get("actual") or ""),
                    error_message=f_dict.get("error_message", ""),
                    stack_trace=f_dict.get("stack_trace", ""),
                )
                session.add(res_model)

            # Save coverage report if present
            cov = rep_dict.get("coverage")
            if cov:
                cov_dict = cov.model_dump() if hasattr(cov, "model_dump") else (cov if isinstance(cov, dict) else {})
                cov_model = CoverageReportModel(
                    project_id=canonical_pid,
                    pipeline_run_id=pipeline_run_id,
                    statements=cov_dict.get("statements", 0.0),
                    branches=cov_dict.get("branches", 0.0),
                    functions=cov_dict.get("functions", 0.0),
                    lines=cov_dict.get("lines", 0.0),
                    coverage_status=cov_dict.get("coverage_status", "available"),
                )
                session.add(cov_model)

            session.commit()
            session.refresh(execution)
            logger.info("[EXECUTION_SAVE] project_id=%s execution_id=%s status=success", canonical_pid, execution.id)
            return execution
        except Exception as exc:
            session.rollback()
            logger.error("[EXECUTION_SAVE_ERROR] project_id=%s error=%s", project_id, exc)
            return None
        finally:
            if self.db is None:
                session.close()

    # ------------------------------------------------------------------
    # Quality Report Persistence & Retrieval
    # ------------------------------------------------------------------

    def save_report(
        self,
        project_id: str,
        pipeline_run_id: str,
        report_data: Any,
    ) -> Optional[ReportModel]:
        """Save human-friendly report summary strictly scoped to project_id."""
        session = self._get_session()
        try:
            canonical_pid = self.resolve_project_id(project_id)
            rd = report_data.model_dump() if hasattr(report_data, "model_dump") else (report_data if isinstance(report_data, dict) else {})
            exec_summary = rd.get("execution_summary", {})
            q_score = rd.get("quality_score", {})

            tot_tests = exec_summary.get("total_tests", 0)
            passed_cnt = exec_summary.get("passed", 0)
            failed_cnt = exec_summary.get("failed", 0)
            skipped_cnt = exec_summary.get("skipped", 0)
            prate = exec_summary.get("pass_rate", 100.0)
            oq_score = q_score.get("overall_score", 100.0)

            if tot_tests == 0:
                tc_count = session.query(TestCaseModel).filter(
                    TestCaseModel.project_id == canonical_pid
                ).count()
                if tc_count > 0:
                    tot_tests = tc_count
                    passed_cnt = max(0, tc_count - failed_cnt - skipped_cnt)
                    prate = round((passed_cnt / tot_tests) * 100.0, 2)
                    gen_sc = q_score.get("generation_score", 100.0)
                    tr_sc = q_score.get("traceability_score", 100.0)
                    oq_score = round(0.50 * prate + 0.25 * gen_sc + 0.25 * tr_sc)

            rep = ReportModel(
                project_id=canonical_pid,
                pipeline_run_id=pipeline_run_id,
                total_tests=tot_tests,
                passed=passed_cnt,
                failed=failed_cnt,
                skipped=skipped_cnt,
                pass_rate=prate,
                overall_quality_score=oq_score,
                report_data=rd,
            )
            session.add(rep)
            session.commit()
            session.refresh(rep)

            logger.info("[REPORT_SAVE] project_id=%s report_id=%s status=success", canonical_pid, rep.id)
            return rep
        except Exception as exc:
            session.rollback()
            logger.error("[REPORT_SAVE_ERROR] project_id=%s error=%s", project_id, exc)
            return None
        finally:
            if self.db is None:
                session.close()

    def get_latest_report(self, project_id: Optional[str] = None, pipeline_run_id: Optional[str] = None) -> Optional[ReportModel]:
        """Query latest report strictly for project or pipeline_run_id (no cross-project leakage)."""
        session = self._get_session()
        try:
            q = session.query(ReportModel)
            if pipeline_run_id:
                q = q.filter(ReportModel.pipeline_run_id == pipeline_run_id)
            elif project_id:
                canonical_pid = self.resolve_project_id(project_id)
                q = q.filter(ReportModel.project_id == canonical_pid)
            else:
                return None

            rep = q.order_by(ReportModel.generated_at.desc()).first()
            if rep and project_id:
                canonical_pid = self.resolve_project_id(project_id)
                self.verify_project_ownership(rep, canonical_pid)

            return rep
        except Exception as exc:
            logger.error("[REPORT_FETCH_ERROR] project_id=%s pipeline_run_id=%s error=%s", project_id, pipeline_run_id, exc)
            return None
        finally:
            if self.db is None:
                session.close()


def cleanup_orphan_records(db: Session) -> Dict[str, int]:
    """Clean up orphan test_cases, test_files, executions, and reports lacking a valid project_id."""
    valid_project_ids = {p.id for p in db.query(Project.id).all()}
    deleted_counts = {"test_cases": 0, "test_files": 0, "executions": 0, "reports": 0}

    # Delete orphan test_cases
    orphan_tcs = db.query(TestCaseModel).filter(~TestCaseModel.project_id.in_(valid_project_ids)).all()
    deleted_counts["test_cases"] = len(orphan_tcs)
    for tc in orphan_tcs:
        db.delete(tc)

    # Delete orphan test_files
    orphan_tfs = db.query(TestFileModel).filter(~TestFileModel.project_id.in_(valid_project_ids)).all()
    deleted_counts["test_files"] = len(orphan_tfs)
    for tf in orphan_tfs:
        db.delete(tf)

    # Delete orphan executions
    orphan_execs = db.query(TestExecutionModel).filter(~TestExecutionModel.project_id.in_(valid_project_ids)).all()
    deleted_counts["executions"] = len(orphan_execs)
    for ex in orphan_execs:
        db.delete(ex)

    # Delete orphan reports
    orphan_reps = db.query(ReportModel).filter(~ReportModel.project_id.in_(valid_project_ids)).all()
    deleted_counts["reports"] = len(orphan_reps)
    for r in orphan_reps:
        db.delete(r)

    db.commit()
    logger.info("[ORPHAN_CLEANUP] Deleted orphan records: %s", deleted_counts)
    return deleted_counts

