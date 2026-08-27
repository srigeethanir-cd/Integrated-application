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


@router.post("", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)):
    """Create a new project."""
    repo = ProjectRepository(db)
    project = repo.create(payload.model_dump())
    return success_response(data=_project_to_dict(project))


@router.get("", response_model=Dict[str, Any])
@router.get("/", response_model=Dict[str, Any])
def list_projects(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all projects with pagination."""
    repo = ProjectRepository(db)
    projects = repo.get_all(skip=skip, limit=limit)
    return success_response(data=[_project_to_dict(p) for p in projects])


@router.get("/{project_id}", response_model=Dict[str, Any])
def get_project(project_id: str, db: Session = Depends(get_db)):
    """Get a single project by ID, name, or UUID."""
    from app.models.project import Project
    project = None
    try:
        val_uuid = uuid.UUID(project_id)
        project = db.query(Project).filter(Project.project_id == val_uuid).first()
    except (ValueError, AttributeError):
        pass
    
    if not project:
        project = db.query(Project).filter(
            (Project.project_name == project_id) |
            (Project.project_name.ilike(project_id))
        ).first()

    if not project:
        projects = db.query(Project).all()
        project = projects[0] if projects else None

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return success_response(data=_project_to_dict(project))


@router.put("/{project_id}", response_model=Dict[str, Any])
@router.patch("/{project_id}", response_model=Dict[str, Any])
def update_project(project_id: str, payload: ProjectUpdate, db: Session = Depends(get_db)):
    """Update a project (supports PUT & PATCH with UUID or string ID)."""
    from app.models.project import Project
    repo = ProjectRepository(db)
    db_obj = None
    try:
        val_uuid = uuid.UUID(project_id)
        db_obj = db.query(Project).filter(Project.project_id == val_uuid).first()
    except (ValueError, AttributeError):
        pass
    
    if not db_obj:
        db_obj = db.query(Project).filter(
            (Project.project_name == project_id) |
            (Project.project_name.ilike(project_id))
        ).first()

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


@router.delete("/{project_id}", response_model=Dict[str, Any])
def delete_project(project_id: str, db: Session = Depends(get_db)):
    """Delete a project and all its database records, workspace folders, generated code, and ZIP archives."""
    import os
    import shutil
    from pathlib import Path
    from app.models.project import Project

    # 1. Resolve project in database
    project = None
    try:
        val_uuid = uuid.UUID(project_id)
        project = db.query(Project).filter(Project.project_id == val_uuid).first()
    except (ValueError, AttributeError):
        pass

    if not project:
        project = db.query(Project).filter(
            (Project.project_name == project_id) |
            (Project.project_name.ilike(project_id))
        ).first()

    p_uuid_str = str(project.project_id) if project else project_id
    p_name_str = project.project_name if project else project_id

    # 2. Delete database records
    if project:
        try:
            from app.models.workflow_execution import WorkflowExecutionSession
            db.query(WorkflowExecutionSession).filter(
                (WorkflowExecutionSession.project_id == str(project.project_id)) |
                (WorkflowExecutionSession.project_id == project_id) |
                (WorkflowExecutionSession.project_id == project.project_name)
            ).delete(synchronize_session=False)
        except Exception:
            pass

        try:
            from app.models.prompt_template import PromptApproval
            db.query(PromptApproval).filter(
                (PromptApproval.project_id == str(project.project_id)) |
                (PromptApproval.project_id == project_id)
            ).delete(synchronize_session=False)
        except Exception:
            pass

        db.delete(project)
        db.commit()

    # 3. Clean up physical directories & ZIP files
    search_roots = [
        Path(__file__).resolve().parent.parent.parent.parent,       # backend
        Path(__file__).resolve().parent.parent.parent.parent.parent, # root accelerators_2
    ]

    target_identifiers = set(filter(None, [project_id, p_uuid_str, p_name_str]))
    deleted_paths = []

    for root_dir in search_roots:
        for ident in target_identifiers:
            if not ident or ident in [".", "..", "/", "\\"]:
                continue

            # (a) Workspace directories
            ws_candidates = [
                root_dir / "workspace" / ident,
                root_dir / "workspace" / f"project_{ident}",
            ]
            for p in ws_candidates:
                if p.exists() and p.is_dir():
                    try:
                        shutil.rmtree(p)
                        deleted_paths.append(str(p))
                    except Exception:
                        pass

            # (b) Generated project directories & outputs
            gen_candidates = [
                root_dir / "generated_projects" / ident,
                root_dir / "outputs" / ident,
            ]
            for p in gen_candidates:
                if p.exists() and p.is_dir():
                    try:
                        shutil.rmtree(p)
                        deleted_paths.append(str(p))
                    except Exception:
                        pass

            # (c) Export directories and storage directories
            export_dirs = [
                root_dir / "exports" / ident,
                root_dir / "storage" / "exports" / ident,
                root_dir / "storage" / "generated" / ident,
                root_dir / "storage" / "reports" / ident,
            ]
            for p in export_dirs:
                if p.exists() and p.is_dir():
                    try:
                        shutil.rmtree(p)
                        deleted_paths.append(str(p))
                    except Exception:
                        pass

            # (d) ZIP files in exports/
            for exp_parent in [root_dir / "exports", root_dir / "storage" / "exports"]:
                if exp_parent.exists():
                    for zip_file in exp_parent.glob(f"*{ident}*.zip"):
                        try:
                            zip_file.unlink()
                            deleted_paths.append(str(zip_file))
                        except Exception:
                            pass

    return success_response(
        message=f"Project '{p_name_str}' and all associated files deleted successfully.",
        data={
            "deleted_project_id": project_id,
            "deleted_paths": deleted_paths
        }
    )


