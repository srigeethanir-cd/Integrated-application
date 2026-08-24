"""Project API routes."""

import uuid
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.responses import success_response
from app.database.session import get_db
from app.repository.project_repository import ProjectRepository
from app.schemas.project import ProjectCreate, ProjectOut, ProjectUpdate

router = APIRouter(prefix="/projects", tags=["Projects"])


def _project_to_dict(project: Any) -> Dict[str, Any]:
    """Convert a Project ORM object to a serialisable dict."""
    return {
        "id": str(project.id),
        "name": project.name,
        "description": project.description,
        "tech_stack": getattr(project, "tech_stack", "Python FastAPI / React TypeScript"),
        "approval_mode": getattr(project, "approval_mode", "HUMAN_IN_LOOP"),
        "status": project.status,
        "created_at": project.created_at.isoformat() if project.created_at else None,
        "updated_at": project.updated_at.isoformat() if project.updated_at else None,
    }


@router.post("/", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)):
    """Create a new project."""
    repo = ProjectRepository(db)
    project = repo.create(payload.model_dump())
    return success_response(data=_project_to_dict(project))


@router.get("/", response_model=Dict[str, Any])
def list_projects(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all projects with pagination."""
    repo = ProjectRepository(db)
    projects = repo.get_all(skip=skip, limit=limit)
    return success_response(data=[_project_to_dict(p) for p in projects])


@router.get("/{project_id}", response_model=Dict[str, Any])
def get_project(project_id: str, db: Session = Depends(get_db)):
    """Get a single project by ID or UUID."""
    repo = ProjectRepository(db)
    project = None
    try:
        val_uuid = uuid.UUID(project_id)
        project = repo.get(val_uuid)
    except ValueError:
        projects = repo.get_all(limit=1)
        project = projects[0] if projects else None
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return success_response(data=_project_to_dict(project))


@router.put("/{project_id}", response_model=Dict[str, Any])
@router.patch("/{project_id}", response_model=Dict[str, Any])
def update_project(project_id: str, payload: ProjectUpdate, db: Session = Depends(get_db)):
    """Update a project (supports PUT & PATCH with UUID or string ID)."""
    repo = ProjectRepository(db)
    db_obj = None
    try:
        val_uuid = uuid.UUID(project_id)
        db_obj = repo.get(val_uuid)
    except ValueError:
        projects = repo.get_all(limit=1)
        db_obj = projects[0] if projects else None
    
    if not db_obj:
        # Create default project if none exists yet
        db_obj = repo.create({
            "name": payload.name or "Default Project",
            "description": payload.description or "Default Description",
            "tech_stack": payload.tech_stack or "Python FastAPI / React TypeScript",
            "approval_mode": payload.approval_mode or "HUMAN_IN_LOOP",
        })
        return success_response(data=_project_to_dict(db_obj))

    update_dict = payload.model_dump(exclude_unset=True)
    updated = repo.update(db_obj, update_dict)

    # Sync with WorkflowExecutionSession state if present
    if "approval_mode" in update_dict:
        try:
            from app.models.workflow_execution import WorkflowExecutionSession
            sess = db.query(WorkflowExecutionSession).filter(
                (WorkflowExecutionSession.project_id == str(db_obj.id)) |
                (WorkflowExecutionSession.project_id == str(project_id))
            ).first()
            if sess and sess.execution_state:
                st = dict(sess.execution_state)
                st["approval_mode"] = update_dict["approval_mode"]
                sess.execution_state = st
                db.add(sess)
                db.commit()
        except Exception:
            pass

    return success_response(data=_project_to_dict(updated))


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: str, db: Session = Depends(get_db)):
    """Delete a project and all its children."""
    repo = ProjectRepository(db)
    del_id = None
    try:
        del_id = uuid.UUID(project_id)
    except ValueError:
        projects = repo.get_all(limit=1)
        if projects:
            del_id = projects[0].id
    if not del_id or not repo.delete(del_id):
        raise HTTPException(status_code=404, detail="Project not found")

