import logging
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from app.repository.prompt_template_repository import PromptTemplateRepository
from app.models.prompt_template import PromptTemplate

logger = logging.getLogger(__name__)

class PromptTemplateService:
    """Coordinates prompt versioning, rollback history, approval states, and telemetry tracking."""

    def __init__(self, db: Session):
        self.db = db
        self.repo = PromptTemplateRepository(db)

    def get_template(self, template_id: str) -> Optional[PromptTemplate]:
        return self.repo.get_by_id(template_id)

    def get_active_prompt(self, prompt_code: str) -> Optional[PromptTemplate]:
        return self.repo.get_by_code(prompt_code)

    def list_templates(self) -> List[PromptTemplate]:
        return self.repo.list_templates()

    def create_template(self, data: Dict[str, Any]) -> PromptTemplate:
        return self.repo.create_template(data)

    def update_template(self, template_id: str, updates: Dict[str, Any], changed_by: str, change_summary: str) -> PromptTemplate:
        template = self.repo.get_by_id(template_id)
        if not template:
            raise ValueError(f"Prompt template {template_id} not found.")
        return self.repo.update_template(template, updates, changed_by, change_summary)

    def approve_prompt(self, template_id: str, reviewer: str, decision: str, comments: str, approved_version: str) -> Dict[str, Any]:
        approval_data = {
            "prompt_template_id": template_id,
            "reviewer": reviewer,
            "decision": decision,
            "comments": comments,
            "approved_version": approved_version
        }
        appr = self.repo.add_approval(approval_data)
        return {
            "success": True,
            "status": decision,
            "approved_at": appr.approved_at.isoformat()
        }

    def rollback_prompt(self, template_id: str, target_version_number: int, changed_by: str) -> Dict[str, Any]:
        template = self.repo.get_by_id(template_id)
        if not template:
            raise ValueError(f"Prompt template {template_id} not found.")

        # Find target version snapshot
        ver = self.repo.get_version(template_id, target_version_number)
        if not ver:
            raise ValueError(f"Version number {target_version_number} not found for template {template_id}.")

        updates = {
            "prompt_template": ver.prompt_snapshot,
            "system_prompt": ver.system_prompt_snapshot,
            "user_prompt": ver.user_prompt_snapshot,
            "model_name": ver.model_snapshot or template.model_name
        }

        change_summary = f"Rolled back to version number {target_version_number} (snapshot of version {ver.previous_version or '1.0'})"
        updated = self.repo.update_template(template, updates, changed_by, change_summary)

        return {
            "success": True,
            "new_version": updated.prompt_version,
            "rolled_back_to": target_version_number
        }

    def list_versions(self, template_id: str) -> List[Any]:
        return self.repo.list_versions(template_id)

    def list_executions(self) -> List[Any]:
        return self.repo.list_executions()

    def list_performance(self) -> List[Any]:
        return self.repo.list_performances()

    def log_execution(self, log_data: Dict[str, Any]):
        self.repo.record_execution(log_data)
