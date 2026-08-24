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
        """List all prompt templates."""
        return self.db.query(PromptTemplate).all()

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
