import uuid
from datetime import datetime, timezone
from typing import Any
from sqlalchemy import Column, String, JSON, Integer, Float, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.hybrid import hybrid_property
from database_main.core.base import Base
from database_main.core.types import GUID, JsonDict

def generate_uuid():
    return str(uuid.uuid4())

class StoryLifecycle(Base):
    """Consolidated model storing execution, validation, approval, and merge lifecycle states of stories."""
    __tablename__ = "story_lifecycles"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    story_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("user_stories.story_id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Execution Fields
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="DRAFT")
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    assigned_agent: Mapped[str] = mapped_column(String(50), nullable=False, default="Agent2")
    execution_time_ms: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    
    # Validation Fields
    validation_type: Mapped[str] = mapped_column(String(50), nullable=False, default="story")
    report: Mapped[Any | None] = mapped_column(JsonDict(), nullable=True)
    
    # Approval Fields
    reviewer: Mapped[str] = mapped_column(String(255), nullable=False, default="Business Analyst")
    comments: Mapped[str | None] = mapped_column(Text, nullable=True)
    decision: Mapped[str] = mapped_column(String(50), nullable=False, default="PENDING")
    
    # Merge Fields
    merged_files: Mapped[Any | None] = mapped_column(JsonDict(), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    story = relationship("Story", back_populates="lifecycle_records")


class StoryHistory(Base):
    """Consolidated model tracking story version snapshots, feedback reviews, and audits."""
    __tablename__ = "story_histories"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    story_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("user_stories.story_id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Version Snapshots
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    code_content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    
    # Audit Logs
    user: Mapped[str] = mapped_column(String(255), nullable=False, default="System")
    agent: Mapped[str] = mapped_column(String(255), nullable=False, default="Orchestrator")
    previous_state: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    new_state: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    comments: Mapped[str | None] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    
    # Feedback & Revisions
    revision_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    author: Mapped[str] = mapped_column(String(255), nullable=False, default="system")
    action: Mapped[str] = mapped_column(String(100), nullable=False, default="audit")
    feedback_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    generation_context: Mapped[Any | None] = mapped_column(JsonDict(), nullable=True)
    files_snapshot: Mapped[Any | None] = mapped_column(JsonDict(), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    story = relationship("Story", back_populates="history_records")


class GeneratedFile(Base):
    """Consolidated model tracking file lists, checksums, history, and version modifications."""
    __tablename__ = "generated_files"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    story_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("user_stories.story_id", ondelete="CASCADE"), nullable=True, index=True)
    component_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("components.id", ondelete="CASCADE"), nullable=True, index=True)
    
    project_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=True, index=True)
    story_key = Column(String(50), nullable=True)
    relative_path = Column(String(500), nullable=False, default="")
    file_path = Column(String(500), nullable=False, default="")
    checksum = Column(String(255), nullable=False, default="")
    ownership = Column(String(255), nullable=False, default="")
    version = Column(Integer, default=1)
    approval_status = Column(String(50), default="PENDING")
    merge_status = Column(String(50), default="PENDING")
    history_json = Column(JSON, default=dict)
    
    # FileHistory content fields
    content = Column(Text, nullable=True)
    action = Column(String(100), nullable=True)
    author = Column(String(255), nullable=True)
    comments = Column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    @property
    def path(self) -> str:
        return self.file_path

    @path.setter
    def path(self, value: str) -> None:
        self.file_path = value

    @property
    def hash(self) -> str | None:
        return self.checksum

    @hash.setter
    def hash(self, value: str | None) -> None:
        self.checksum = value or ""

    story = relationship("Story", back_populates="files")
    component = relationship("Component", back_populates="files")

    @hybrid_property
    def path(self):
        return self.relative_path

    @path.setter
    def path(self, value):
        self.relative_path = value
        self.file_path = value

    @hybrid_property
    def hash(self):
        return self.checksum

    @hash.setter
    def hash(self, value):
        self.checksum = value



class Artifact(Base):
    """Consolidated model storing generated code artifact content and shared registry entries."""
    __tablename__ = "artifacts"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    story_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("user_stories.story_id", ondelete="CASCADE"), nullable=True, index=True)
    
    project_id = Column(GUID(), nullable=True, index=True)
    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False, default="common")
    file_path = Column(String(500), nullable=False)
    owner_story = Column(String(50), nullable=True)
    shared_flag = Column(Boolean, default=False)
    version = Column(Integer, default=1)
    checksum = Column(String(255), nullable=True)
    content = Column(Text, nullable=True)
    usage_references_json = Column(JSON, default=list)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    story = relationship("Story", back_populates="artifacts")
    project = relationship("Project", primaryjoin="Artifact.project_id == Project.project_id", foreign_keys=[project_id], overlaps="artifacts")



class StoryDependency(Base):
    """Consolidated model mapping story-level relationship linkages and project execution order DAG graphs."""
    __tablename__ = "story_dependencies"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    story_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("user_stories.story_id", ondelete="CASCADE"), nullable=True, index=True)
    
    dependency_story_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), nullable=True)
    relation_type: Mapped[str | None] = mapped_column(String(50), nullable=True)

    project_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=True, index=True)
    component_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("components.id", ondelete="CASCADE"), nullable=True, index=True)
    depends_on_component_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("components.id", ondelete="CASCADE"), nullable=True, index=True)

    source_story = Column(String(50), nullable=True)
    target_story = Column(String(50), nullable=True)
    dependency_type = Column(String(50), nullable=True)
    dependency_graph_json = Column(JSON, default=dict)
    execution_order_json = Column(JSON, default=list)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    story = relationship("Story", back_populates="dependencies")

    component = relationship("Component", foreign_keys=[component_id], back_populates="dependencies_out")
    depends_on_component = relationship("Component", foreign_keys=[depends_on_component_id], back_populates="dependencies_in")


class ExecutionLog(Base):
    """Consolidated model tracking execution timelines, scheduler queue loops, and agent metrics."""
    __tablename__ = "execution_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(GUID(), ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False, index=True)
    story_key = Column(String(50), nullable=True)
    agent_name = Column(String(100), nullable=False, default="Orchestrator")
    stage = Column(String(100), nullable=True)
    
    # Support both execution_status (ExecutionTimelineRecord) and execution_state (AgentExecutionMetric)
    execution_state = Column(String(100), nullable=False, default="SUCCESS")
    inputs_json = Column(JSON, default=dict)
    outputs_json = Column(JSON, default=dict)
    scheduler_state_json = Column(JSON, default=dict)
    timeline_events_json = Column(JSON, default=list)
    timings_sec = Column(Float, default=0.0)
    retries_count = Column(Integer, default=0)
    version = Column(String(50), default="1.0")

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Add single-table inheritance discriminator
    record_type = Column(String(50), nullable=False, default="generic")

    __mapper_args__ = {
        "polymorphic_on": "record_type",
        "polymorphic_identity": "generic",
    }

    @property
    def execution_status(self) -> str:
        return self.execution_state

    @execution_status.setter
    def execution_status(self, value: str) -> None:
        self.execution_state = value

    @property
    def retry_count(self) -> int:
        return self.retries_count

    @retry_count.setter
    def retry_count(self, value: int) -> None:
        self.retries_count = value


class ExecutionTimelineRecord(ExecutionLog):
    __tablename__ = None
    __mapper_args__ = {
        "polymorphic_identity": "timeline",
    }


class AgentExecutionMetric(ExecutionLog):
    __tablename__ = None
    __mapper_args__ = {
        "polymorphic_identity": "metric",
    }


class ProjectValidation(Base):
    """Consolidated model tracking validation scores, test coverage, and health metrics."""
    __tablename__ = "project_validations"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    story_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("user_stories.story_id", ondelete="CASCADE"), nullable=True, index=True)
    
    project_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=True, index=True)
    build_status = Column(String(50), nullable=True)
    validation_status = Column(String(50), nullable=True)
    security_status = Column(String(50), nullable=True)
    test_coverage = Column(String(20), nullable=True)
    metrics_json = Column(JSON, default=dict)
    validation_score = Column(Float, default=100.0)
    
    # ValidationResult fields
    validator_name = Column(String(100), nullable=True)
    report = Column(JSON, default=dict)
    passed = Column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    story = relationship("Story")


class StoryRefinement(Base):
    """Consolidated model tracking user story refinement prompts and version logs."""
    __tablename__ = "story_refinements"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    story_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("user_stories.story_id", ondelete="CASCADE"), nullable=False, index=True)
    version_id: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    refinement_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    previous_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    new_version: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    created_by: Mapped[str] = mapped_column(String(255), nullable=False, default="Business Analyst")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    story = relationship("Story")
