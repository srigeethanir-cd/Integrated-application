import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.core.responses import success_response
from app.services.prompt_template_service import PromptTemplateService

router = APIRouter(prefix="/prompt-templates", tags=["Prompt Templates"])
logger = logging.getLogger(__name__)

# Pydantic schemas
class PromptTemplateCreate(BaseModel):
    prompt_code: str = Field(..., description="Unique prompt identifier code")
    prompt_name: str = Field(..., description="Human readable name of prompt")
    description: Optional[str] = None
    agent_name: str = Field(..., description="Target agent name")
    prompt_template: str = Field(..., description="Raw prompt template text")
    system_prompt: Optional[str] = None
    user_prompt: Optional[str] = None
    temperature: Optional[float] = 0.2
    max_tokens: Optional[int] = 1024
    created_by: Optional[str] = "admin"

class PromptTemplateUpdate(BaseModel):
    prompt_name: Optional[str] = None
    description: Optional[str] = None
    prompt_template: Optional[str] = None
    system_prompt: Optional[str] = None
    user_prompt: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    changed_by: str = Field("admin", description="Who changed the template")
    change_summary: str = Field(..., description="Summary of the changes made")

class PromptApprovalRequest(BaseModel):
    reviewer: str = Field(..., description="Who reviewed and decided")
    decision: str = Field(..., description="Decision: Approved, Rejected")
    comments: Optional[str] = None
    approved_version: str = Field(..., description="Version string approved")

class PromptRollbackRequest(BaseModel):
    target_version_number: int = Field(..., description="Version number to restore")
    changed_by: str = Field(..., description="Who triggered rollback")

def _template_to_dict(t: Any) -> Dict[str, Any]:
    return {
        "id": t.id,
        "prompt_code": t.prompt_code,
        "prompt_name": t.prompt_name,
        "description": t.description,
        "agent_name": t.agent_name,
        "agent_version": t.agent_version,
        "llm_provider": t.llm_provider,
        "model_name": t.model_name,
        "prompt_category": t.prompt_category,
        "prompt_template": t.prompt_template,
        "prompt_variables": t.prompt_variables,
        "system_prompt": t.system_prompt,
        "user_prompt": t.user_prompt,
        "temperature": t.temperature,
        "max_tokens": t.max_tokens,
        "prompt_version": t.prompt_version,
        "status": t.status,
        "is_active": t.is_active,
        "created_by": t.created_by,
        "created_at": t.created_at.isoformat() if t.created_at else None,
        "updated_at": t.updated_at.isoformat() if t.updated_at else None,
    }

@router.get("", response_model=Dict[str, Any])
def list_templates(db: Session = Depends(get_db)):
    """List all prompt templates in the system."""
    service = PromptTemplateService(db)
    templates = service.list_templates()
    return success_response(data=[_template_to_dict(t) for t in templates])

@router.get("/{template_id}", response_model=Dict[str, Any])
def get_template(template_id: str, db: Session = Depends(get_db)):
    """Fetch details of a specific prompt template by ID."""
    service = PromptTemplateService(db)
    template = service.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Prompt template not found")
    return success_response(data=_template_to_dict(template))

@router.post("", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
def create_template(payload: PromptTemplateCreate, db: Session = Depends(get_db)):
    """Create a new prompt template and insert version 1.0 snapshot."""
    service = PromptTemplateService(db)
    try:
        t = service.create_template(payload.model_dump())
        return success_response(data=_template_to_dict(t))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{template_id}", response_model=Dict[str, Any])
def update_template(template_id: str, payload: PromptTemplateUpdate, db: Session = Depends(get_db)):
    """Update a prompt template and increment its version."""
    service = PromptTemplateService(db)
    try:
        updates = payload.model_dump(exclude_unset=True)
        changed_by = updates.pop("changed_by", "admin")
        change_summary = updates.pop("change_summary", "Modified template")
        t = service.update_template(template_id, updates, changed_by, change_summary)
        return success_response(data=_template_to_dict(t))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{template_id}", response_model=Dict[str, Any])
def delete_template(template_id: str, db: Session = Depends(get_db)):
    """Soft delete or archive a prompt template."""
    service = PromptTemplateService(db)
    template = service.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Prompt template not found")
    
    # Soft delete / archive
    template.is_active = False
    template.status = "Archived"
    db.commit()
    return success_response(data=_template_to_dict(template), message="Prompt template archived successfully")

@router.post("/{template_id}/approve", response_model=Dict[str, Any])
def approve_template(template_id: str, payload: PromptApprovalRequest, db: Session = Depends(get_db)):
    """Approve or reject a prompt template version."""
    service = PromptTemplateService(db)
    try:
        res = service.approve_prompt(
            template_id=template_id,
            reviewer=payload.reviewer,
            decision=payload.decision,
            comments=payload.comments,
            approved_version=payload.approved_version
        )
        return success_response(data=res, message=f"Prompt template version marked as {payload.decision}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{template_id}/rollback", response_model=Dict[str, Any])
def rollback_template(template_id: str, payload: PromptRollbackRequest, db: Session = Depends(get_db)):
    """Roll back a prompt template to a previous version."""
    service = PromptTemplateService(db)
    try:
        res = service.rollback_prompt(
            template_id=template_id,
            target_version_number=payload.target_version_number,
            changed_by=payload.changed_by
        )
        return success_response(data=res, message="Prompt template rolled back successfully")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{template_id}/versions", response_model=Dict[str, Any])
def get_template_versions(template_id: str, db: Session = Depends(get_db)):
    """Fetch version history lists of a prompt template."""
    service = PromptTemplateService(db)
    versions = service.list_versions(template_id)
    v_list = []
    for v in versions:
        v_list.append({
            "id": v.id,
            "version_number": v.version_number,
            "previous_version": v.previous_version,
            "prompt_snapshot": v.prompt_snapshot,
            "system_prompt_snapshot": v.system_prompt_snapshot,
            "user_prompt_snapshot": v.user_prompt_snapshot,
            "model_snapshot": v.model_snapshot,
            "change_summary": v.change_summary,
            "changed_by": v.changed_by,
            "created_at": v.created_at.isoformat() if v.created_at else None
        })
    return success_response(data=v_list)

# Expose global reporting logs under custom prefix tag-endpoints
@router.get("/executions", response_model=Dict[str, Any])
def get_executions(db: Session = Depends(get_db)):
    """Global execution logs telemetry retrieval."""
    service = PromptTemplateService(db)
    logs = service.list_executions()
    res_list = []
    for l in logs:
        res_list.append({
            "id": l.id,
            "project_id": l.project_id,
            "story_id": l.story_id,
            "prompt_template_id": l.prompt_template_id,
            "prompt_version": l.prompt_version,
            "agent_name": l.agent_name,
            "llm_provider": l.llm_provider,
            "model_name": l.model_name,
            "input_tokens": l.input_tokens,
            "output_tokens": l.output_tokens,
            "total_tokens": l.total_tokens,
            "estimated_cost": l.estimated_cost,
            "execution_time_ms": l.execution_time_ms,
            "execution_status": l.execution_status,
            "generated_at": l.generated_at.isoformat() if l.generated_at else None
        })
    return success_response(data=res_list)

@router.get("/performance", response_model=Dict[str, Any])
def get_performance(db: Session = Depends(get_db)):
    """Fetch performance logs of active prompt templates."""
    service = PromptTemplateService(db)
    perfs = service.list_performance()
    res_list = []
    for p in perfs:
        res_list.append({
            "id": p.id,
            "prompt_template_id": p.prompt_template_id,
            "total_runs": p.total_runs,
            "successful_runs": p.successful_runs,
            "failed_runs": p.failed_runs,
            "average_execution_time": p.average_execution_time,
            "average_tokens": p.average_tokens,
            "average_cost": p.average_cost,
            "average_validation_score": p.average_validation_score,
            "regeneration_rate": p.regeneration_rate,
            "last_updated": p.last_updated.isoformat() if p.last_updated else None
        })
    return success_response(data=res_list)
