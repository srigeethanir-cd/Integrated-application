import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.prompt_template import (
    PromptTemplate,
    PromptTemplateVersion,
    PromptExecutionLog,
    PromptApproval,
    PromptPerformance
)

logger = logging.getLogger(__name__)

class PromptTemplateRepository:
    """Repository handling all prompt templates and metrics operations in PostgreSQL."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_code(self, prompt_code: str) -> Optional[PromptTemplate]:
        """Fetch active approved prompt template by code."""
        return self.db.query(PromptTemplate).filter_by(prompt_code=prompt_code, is_active=True).first()

    def get_by_id(self, template_id: str) -> Optional[PromptTemplate]:
        """Fetch prompt template by ID."""
        return self.db.query(PromptTemplate).filter_by(id=template_id).first()

    def list_templates(self) -> List[PromptTemplate]:
        """List all prompt templates, seeding defaults if empty."""
        existing = self.db.query(PromptTemplate).all()
        if existing:
            return existing

        # Auto-seed default real agent prompt templates
        defaults = [
            {
                "prompt_code": "AGENT1_BLUEPRINT_ARCHITECT",
                "prompt_name": "Agent 1 Blueprint Planner",
                "description": "Generates comprehensive enterprise software architecture blueprints, schemas, and API contracts.",
                "agent_name": "Agent 1",
                "agent_version": "v1.4",
                "llm_provider": "OpenAI",
                "model_name": "gpt-4o",
                "prompt_category": "Architecture",
                "prompt_template": "You are a senior software architect. Analyze the user story and generate fully compliant frontend and backend architecture modules under the core framework directory.",
                "system_prompt": "You are a Principal Software Architect. Design clean, scalable, decoupled architectures adhering to RESTful standards and SQLAlchemy ORM conventions.",
                "user_prompt": "Analyze requirement specifications and generate structured blueprint manifests.",
                "temperature": 0.2,
                "max_tokens": 2048,
                "prompt_version": "1.4",
                "created_by": "System Architect"
            },
            {
                "prompt_code": "AGENT2_FRONTEND_BUILDER",
                "prompt_name": "Agent 2 Frontend Builder",
                "description": "Generates production-grade React 18, Vite, and TypeScript components with TailwindCSS styles.",
                "agent_name": "Agent 2",
                "agent_version": "v2.1",
                "llm_provider": "OpenAI",
                "model_name": "gpt-4o-mini",
                "prompt_category": "Frontend",
                "prompt_template": "You are an expert frontend engineer. Generate complete production-ready React 18 and TypeScript components with responsive Tailwind CSS layout.",
                "system_prompt": "You are an expert React TypeScript developer. Write complete, compile-clean React components with proper props interfaces and state management.",
                "user_prompt": "Generate React UI components implementing the active user story.",
                "temperature": 0.2,
                "max_tokens": 4096,
                "prompt_version": "2.1",
                "created_by": "Frontend Lead"
            },
            {
                "prompt_code": "AGENT2_BACKEND_BUILDER",
                "prompt_name": "Agent 2 Backend Builder",
                "description": "Generates asynchronous FastAPI routers, Pydantic schemas, SQLAlchemy models, and business services.",
                "agent_name": "Agent 2",
                "agent_version": "v2.0",
                "llm_provider": "OpenAI",
                "model_name": "gpt-4o-mini",
                "prompt_category": "Backend",
                "prompt_template": "You are an expert backend engineer. Generate complete asynchronous FastAPI endpoints, Pydantic v2 validation models, and SQLAlchemy 2.0 database queries.",
                "system_prompt": "You are a Senior FastAPI engineer. Write production-ready Python code with async endpoints, dependency injection, and complete CRUD business logic.",
                "user_prompt": "Generate FastAPI routers and SQLAlchemy models for the active user story.",
                "temperature": 0.2,
                "max_tokens": 4096,
                "prompt_version": "2.0",
                "created_by": "Backend Lead"
            },
            {
                "prompt_code": "AGENT2_TEST_BUILDER",
                "prompt_name": "Agent 2 Pytest Test Builder",
                "description": "Generates comprehensive Pytest unit and integration tests with complete coverage.",
                "agent_name": "Agent 2",
                "agent_version": "v1.2",
                "llm_provider": "OpenAI",
                "model_name": "gpt-4o-mini",
                "prompt_category": "Testing",
                "prompt_template": "You are a senior QA automation engineer. Generate unit and API integration tests using pytest, pytest-asyncio, and TestClient with complete assertion coverage.",
                "system_prompt": "You are a QA automation expert. Write robust unit tests verifying happy paths, edge cases, and error responses.",
                "user_prompt": "Generate test_*.py test suites for the story endpoints.",
                "temperature": 0.2,
                "max_tokens": 2048,
                "prompt_version": "1.2",
                "created_by": "QA Architect"
            },
            {
                "prompt_code": "AGENT3_CODE_VALIDATOR",
                "prompt_name": "Agent 3 Code Validator & Auditor",
                "description": "Validates AST syntax, security vulnerabilities, SQL injection risks, and cross-story compatibility.",
                "agent_name": "Agent 3",
                "agent_version": "v1.0",
                "llm_provider": "OpenAI",
                "model_name": "gpt-4o",
                "prompt_category": "Governance",
                "prompt_template": "You are a principal code auditor. Validate AST syntax correctness, security vulnerabilities, SQL injection risks, and cross-story compatibility.",
                "system_prompt": "You are a Code Governance Auditor. Inspect generated source files for compliance with project blueprints and security policies.",
                "user_prompt": "Audit generated code and produce comprehensive validation reports.",
                "temperature": 0.1,
                "max_tokens": 2048,
                "prompt_version": "1.0",
                "created_by": "Governance Lead"
            }
        ]

        seeded = []
        for d in defaults:
            t = self.create_template(d)
            seeded.append(t)
        return seeded

    def create_template(self, data: Dict[str, Any]) -> PromptTemplate:
        """Create a new prompt template and insert version 1.0 snapshot."""
        template = PromptTemplate(**data)
        self.db.add(template)
        self.db.flush()  # Generate ID

        # Create Version 1.0 snapshot record
        ver = PromptTemplateVersion(
            prompt_template_id=template.id,
            version_number=1,
            previous_version=None,
            prompt_snapshot=template.prompt_template,
            system_prompt_snapshot=template.system_prompt,
            user_prompt_snapshot=template.user_prompt,
            model_snapshot=template.model_name,
            change_summary="Initial template creation",
            changed_by=template.created_by
        )
        self.db.add(ver)

        # Create Performance registry
        perf = PromptPerformance(prompt_template_id=template.id)
        self.db.add(perf)

        self.db.commit()
        return template

    def update_template(self, template: PromptTemplate, updates: Dict[str, Any], changed_by: str, change_summary: str) -> PromptTemplate:
        """Update template, increment version number and append to Version history."""
        # Calculate new version number
        try:
            current_ver_num = float(template.prompt_version)
        except ValueError:
            current_ver_num = 1.0
        new_ver_str = f"{current_ver_num + 0.1:.1f}"

        prev_ver_str = template.prompt_version

        # Apply updates
        for key, value in updates.items():
            setattr(template, key, value)
        
        template.prompt_version = new_ver_str
        template.updated_by = changed_by
        template.updated_at = datetime.now(timezone.utc)

        # Write Template Version History
        ver = PromptTemplateVersion(
            prompt_template_id=template.id,
            version_number=len(self.list_versions(template.id)) + 1,
            previous_version=prev_ver_str,
            prompt_snapshot=template.prompt_template,
            system_prompt_snapshot=template.system_prompt,
            user_prompt_snapshot=template.user_prompt,
            model_snapshot=template.model_name,
            change_summary=change_summary,
            changed_by=changed_by
        )
        self.db.add(ver)
        self.db.commit()
        return template

    def list_versions(self, template_id: str) -> List[PromptTemplateVersion]:
        """Fetch all versions of a prompt template."""
        return self.db.query(PromptTemplateVersion).filter_by(prompt_template_id=template_id).order_by(PromptTemplateVersion.version_number.asc()).all()

    def get_version(self, template_id: str, version_number: int) -> Optional[PromptTemplateVersion]:
        """Fetch specific version snapshot."""
        return self.db.query(PromptTemplateVersion).filter_by(prompt_template_id=template_id, version_number=version_number).first()

    def record_execution(self, log_data: Dict[str, Any]):
        """Append prompt execution telemetry log and update performance averages."""
        log = PromptExecutionLog(**log_data)
        self.db.add(log)
        self.db.flush()

        # Update performance metrics
        perf = self.db.query(PromptPerformance).filter_by(prompt_template_id=log.prompt_template_id).first()
        if not perf:
            perf = PromptPerformance(prompt_template_id=log.prompt_template_id)
            self.db.add(perf)

        perf.total_runs += 1
        if log.execution_status == "SUCCESS":
            perf.successful_runs += 1
        else:
            perf.failed_runs += 1

        # Re-calculate averages
        runs = perf.total_runs
        if runs > 0:
            perf.average_execution_time = (perf.average_execution_time * (runs - 1) + log.execution_time_ms) / runs
            perf.average_tokens = (perf.average_tokens * (runs - 1) + log.total_tokens) / runs
            perf.average_cost = (perf.average_cost * (runs - 1) + log.estimated_cost) / runs
            if log.retry_count > 0:
                perf.regeneration_rate = perf.failed_runs / runs

        self.db.commit()

    def add_approval(self, approval_data: Dict[str, Any]) -> PromptApproval:
        """Create prompt approval decision log."""
        appr = PromptApproval(**approval_data)
        self.db.add(appr)
        
        # If approved, update template status
        template = self.get_by_id(appr.prompt_template_id)
        if template:
            template.status = appr.decision
            if appr.decision == "Approved":
                template.is_active = True
                
        self.db.commit()
        return appr

    def list_executions(self) -> List[PromptExecutionLog]:
        """Fetch all execution logs."""
        return self.db.query(PromptExecutionLog).order_by(PromptExecutionLog.generated_at.desc()).limit(100).all()

    def list_performances(self) -> List[PromptPerformance]:
        """Fetch all performance metrics."""
        return self.db.query(PromptPerformance).all()
