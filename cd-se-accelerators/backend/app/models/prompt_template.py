import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, JSON, Integer, Float, DateTime, ForeignKey, Boolean, Text
from app.models.project import Base
from app.database.types import GUID

def generate_uuid():
    return str(uuid.uuid4())

class PromptTemplate(Base):
    __tablename__ = "prompt_templates"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    prompt_code = Column(String(100), unique=True, nullable=False)
    prompt_name = Column(String(255), nullable=False)
    description = Column(String(1000), nullable=True)
    agent_name = Column(String(100), nullable=False)
    agent_version = Column(String(50), default="1.0")
    llm_provider = Column(String(100), default="groq")
    model_name = Column(String(100), default="llama-3.3-70b-versatile")
    prompt_category = Column(String(100), default="generation")
    prompt_template = Column(Text, nullable=False)
    prompt_variables = Column(JSON, default=list)
    system_prompt = Column(Text, nullable=True)
    user_prompt = Column(Text, nullable=True)
    output_schema = Column(JSON, default=dict)
    temperature = Column(Float, default=0.2)
    max_tokens = Column(Integer, default=1024)
    top_p = Column(Float, default=1.0)
    frequency_penalty = Column(Float, default=0.0)
    presence_penalty = Column(Float, default=0.0)
    prompt_version = Column(String(50), default="1.0")
    status = Column(String(50), default="Approved")  # Draft, Pending Review, Approved, Deprecated, Archived
    is_active = Column(Boolean, default=True)
    created_by = Column(String(255), default="system")
    updated_by = Column(String(255), default="system")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class PromptTemplateVersion(Base):
    __tablename__ = "prompt_template_versions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    prompt_template_id = Column(String(36), nullable=False)
    version_number = Column(Integer, nullable=False)
    previous_version = Column(String(50), nullable=True)
    prompt_snapshot = Column(Text, nullable=False)
    system_prompt_snapshot = Column(Text, nullable=True)
    user_prompt_snapshot = Column(Text, nullable=True)
    model_snapshot = Column(String(100), nullable=True)
    change_summary = Column(String(1000), nullable=True)
    changed_by = Column(String(255), default="system")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class PromptExecutionLog(Base):
    __tablename__ = "prompt_execution_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(GUID(), ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=True, index=True)
    epic_id = Column(String(255), nullable=True)
    story_id = Column(String(255), nullable=True)
    execution_id = Column(String(255), nullable=True)
    prompt_template_id = Column(String(36), nullable=False)
    prompt_version = Column(String(50), nullable=False)
    agent_name = Column(String(100), nullable=False)
    llm_provider = Column(String(100), nullable=False)
    model_name = Column(String(100), nullable=False)
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    estimated_cost = Column(Float, default=0.0)
    execution_time_ms = Column(Integer, default=0)
    execution_status = Column(String(50), default="SUCCESS")
    retry_count = Column(Integer, default=0)
    generated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class PromptApproval(Base):
    __tablename__ = "prompt_approvals"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    prompt_template_id = Column(String(36), nullable=False)
    reviewer = Column(String(255), nullable=False)
    decision = Column(String(50), nullable=False)  # Approved, Rejected
    comments = Column(String(1000), nullable=True)
    approved_version = Column(String(50), nullable=False)
    approved_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    bundle_json = Column(JSON, nullable=True)



class PromptPerformance(Base):
    __tablename__ = "prompt_performances"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    prompt_template_id = Column(String(36), nullable=False)
    total_runs = Column(Integer, default=0)
    successful_runs = Column(Integer, default=0)
    failed_runs = Column(Integer, default=0)
    average_execution_time = Column(Float, default=0.0)
    average_tokens = Column(Float, default=0.0)
    average_cost = Column(Float, default=0.0)
    average_validation_score = Column(Float, default=0.0)
    regeneration_rate = Column(Float, default=0.0)
    last_updated = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
