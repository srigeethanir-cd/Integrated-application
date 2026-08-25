"""
SQLAlchemy ORM Models – Persistent Neon PostgreSQL Schema.

Defines tables for Projects, Pipeline Runs, Source Files, Components,
Test Cases, Test Files, Test Executions, Test Results, Coverage Reports, and Reports.
Includes indexes and foreign key constraints for project_id, pipeline_run_id, component_id, test_case_id.
"""

from datetime import datetime
import uuid
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    Text,
    DateTime,
    ForeignKey,
    JSON,
    Index,
)
from sqlalchemy.orm import relationship

from app.db.database import Base


def generate_uuid() -> str:
    """Generate string UUID primary key."""
    return str(uuid.uuid4())


class Project(Base):
    """projects table."""

    __tablename__ = "projects"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    project_name = Column(String(255), nullable=False)
    framework = Column(String(64), nullable=True, default="React")
    project_path = Column(String(1024), nullable=False)
    workspace_path = Column(String(1024), nullable=True)
    status = Column(String(64), nullable=False, default="created")
    source_file_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    pipeline_runs = relationship("PipelineRun", back_populates="project", cascade="all, delete-orphan")
    source_files = relationship("SourceFile", back_populates="project", cascade="all, delete-orphan")
    components = relationship("Component", back_populates="project", cascade="all, delete-orphan")
    test_cases = relationship("TestCaseModel", back_populates="project", cascade="all, delete-orphan")
    test_files = relationship("TestFileModel", back_populates="project", cascade="all, delete-orphan")
    test_executions = relationship("TestExecutionModel", back_populates="project", cascade="all, delete-orphan")
    coverage_reports = relationship("CoverageReportModel", back_populates="project", cascade="all, delete-orphan")
    reports = relationship("ReportModel", back_populates="project", cascade="all, delete-orphan")


class PipelineRun(Base):
    """pipeline_runs table."""

    __tablename__ = "pipeline_runs"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    project_id = Column(String(64), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(64), nullable=False, default="running")
    current_stage = Column(String(128), nullable=False, default="source_ingestion")
    progress = Column(Float, default=0.0)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)

    # Relationships
    project = relationship("Project", back_populates="pipeline_runs")
    source_files = relationship("SourceFile", back_populates="pipeline_run", cascade="all, delete-orphan")
    components = relationship("Component", back_populates="pipeline_run", cascade="all, delete-orphan")
    test_cases = relationship("TestCaseModel", back_populates="pipeline_run", cascade="all, delete-orphan")
    test_files = relationship("TestFileModel", back_populates="pipeline_run", cascade="all, delete-orphan")
    test_executions = relationship("TestExecutionModel", back_populates="pipeline_run", cascade="all, delete-orphan")
    coverage_reports = relationship("CoverageReportModel", back_populates="pipeline_run", cascade="all, delete-orphan")
    reports = relationship("ReportModel", back_populates="pipeline_run", cascade="all, delete-orphan")


class SourceFile(Base):
    """source_files table."""

    __tablename__ = "source_files"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    project_id = Column(String(64), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    pipeline_run_id = Column(String(64), ForeignKey("pipeline_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    file_path = Column(String(1024), nullable=False)
    file_hash = Column(String(128), nullable=True)
    file_type = Column(String(64), nullable=True)
    analyzed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="source_files")
    pipeline_run = relationship("PipelineRun", back_populates="source_files")
    components = relationship("Component", back_populates="source_file")


class Component(Base):
    """components table."""

    __tablename__ = "components"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    project_id = Column(String(64), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    pipeline_run_id = Column(String(64), ForeignKey("pipeline_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    source_file_id = Column(String(64), ForeignKey("source_files.id", ondelete="SET NULL"), nullable=True, index=True)
    component_type = Column(String(128), nullable=True, default="ReactComponent")
    framework = Column(String(64), nullable=True, default="React")
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="components")
    pipeline_run = relationship("PipelineRun", back_populates="components")
    source_file = relationship("SourceFile", back_populates="components")
    test_cases = relationship("TestCaseModel", back_populates="component_rel")
    test_files = relationship("TestFileModel", back_populates="component_rel")


class TestCaseModel(Base):
    """test_cases table."""

    __test__ = False
    __tablename__ = "test_cases"

    id = Column(String(128), primary_key=True)  # e.g. TC-LOGIN-001 or UUID
    project_id = Column(String(64), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    pipeline_run_id = Column(String(64), ForeignKey("pipeline_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    component_id = Column(String(64), ForeignKey("components.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(512), nullable=False)
    objective = Column(Text, nullable=True)
    specification = Column(Text, nullable=True)
    category = Column(String(128), nullable=True, default="General")
    priority = Column(String(64), nullable=True, default="Medium")
    steps = Column(JSON, nullable=True)
    expected_result = Column(Text, nullable=True)
    source_function = Column(String(255), nullable=True)
    status = Column(String(64), nullable=False, default="generated")
    quality_score = Column(Integer, nullable=True, default=100)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="test_cases")
    pipeline_run = relationship("PipelineRun", back_populates="test_cases")
    component_rel = relationship("Component", back_populates="test_cases")
    test_results = relationship("TestResultModel", back_populates="test_case")


class TestFileModel(Base):
    """test_files table."""

    __test__ = False
    __tablename__ = "test_files"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    project_id = Column(String(64), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    pipeline_run_id = Column(String(64), ForeignKey("pipeline_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    component_id = Column(String(64), ForeignKey("components.id", ondelete="SET NULL"), nullable=True, index=True)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(1024), nullable=False)
    framework = Column(String(64), nullable=True, default="React")
    test_case_ids = Column(JSON, nullable=True)
    generated_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="test_files")
    pipeline_run = relationship("PipelineRun", back_populates="test_files")
    component_rel = relationship("Component", back_populates="test_files")
    test_executions = relationship("TestExecutionModel", back_populates="test_file")


class TestExecutionModel(Base):
    """test_executions table."""

    __test__ = False
    __tablename__ = "test_executions"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    project_id = Column(String(64), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    pipeline_run_id = Column(String(64), ForeignKey("pipeline_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    test_file_id = Column(String(64), ForeignKey("test_files.id", ondelete="SET NULL"), nullable=True, index=True)
    status = Column(String(64), nullable=False, default="completed")
    total_tests = Column(Integer, default=0)
    passed = Column(Integer, default=0)
    failed = Column(Integer, default=0)
    skipped = Column(Integer, default=0)
    execution_time_ms = Column(Float, default=0.0)
    pass_rate = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="test_executions")
    pipeline_run = relationship("PipelineRun", back_populates="test_executions")
    test_file = relationship("TestFileModel", back_populates="test_executions")
    results = relationship("TestResultModel", back_populates="execution", cascade="all, delete-orphan")


class TestResultModel(Base):
    """test_results table."""

    __test__ = False
    __tablename__ = "test_results"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    execution_id = Column(String(64), ForeignKey("test_executions.id", ondelete="CASCADE"), nullable=False, index=True)
    test_case_id = Column(String(128), ForeignKey("test_cases.id", ondelete="SET NULL"), nullable=True, index=True)
    test_name = Column(String(512), nullable=False)
    status = Column(String(64), nullable=False, default="passed")
    expected = Column(Text, nullable=True)
    actual = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    stack_trace = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    execution = relationship("TestExecutionModel", back_populates="results")
    test_case = relationship("TestCaseModel", back_populates="test_results")


class CoverageReportModel(Base):
    """coverage_reports table."""

    __tablename__ = "coverage_reports"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    project_id = Column(String(64), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    pipeline_run_id = Column(String(64), ForeignKey("pipeline_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    statements = Column(Float, default=0.0)
    branches = Column(Float, default=0.0)
    functions = Column(Float, default=0.0)
    lines = Column(Float, default=0.0)
    coverage_status = Column(String(64), nullable=True, default="available")
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="coverage_reports")
    pipeline_run = relationship("PipelineRun", back_populates="coverage_reports")


class ReportModel(Base):
    """reports table."""

    __tablename__ = "reports"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    project_id = Column(String(64), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    pipeline_run_id = Column(String(64), ForeignKey("pipeline_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    total_tests = Column(Integer, default=0)
    passed = Column(Integer, default=0)
    failed = Column(Integer, default=0)
    skipped = Column(Integer, default=0)
    pass_rate = Column(Float, default=0.0)
    overall_quality_score = Column(Float, default=0.0)
    report_data = Column(JSON, nullable=True)
    generated_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="reports")
    pipeline_run = relationship("PipelineRun", back_populates="reports")


# Composite indexes for multi-column project isolation queries
Index("idx_source_files_proj_run", SourceFile.project_id, SourceFile.pipeline_run_id)
Index("idx_components_proj_run", Component.project_id, Component.pipeline_run_id)
Index("idx_test_cases_proj_run", TestCaseModel.project_id, TestCaseModel.pipeline_run_id)
Index("idx_test_files_proj_run", TestFileModel.project_id, TestFileModel.pipeline_run_id)
Index("idx_executions_proj_run", TestExecutionModel.project_id, TestExecutionModel.pipeline_run_id)
Index("idx_coverage_proj_run", CoverageReportModel.project_id, CoverageReportModel.pipeline_run_id)
Index("idx_reports_proj_run", ReportModel.project_id, ReportModel.pipeline_run_id)
