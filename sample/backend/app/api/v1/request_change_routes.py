"""RequestChange API routes."""

import uuid
from typing import Any, Dict, List
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.request_change import RequestChange
from app.models.epic import Epic as EpicModel
from app.models.story import Story as StoryModel
from app.models.blueprint import Blueprint as BlueprintModel
from app.repository.request_change_repository import RequestChangeRepository
from app.schemas.ba_accelerator import RequestChangeCreate, RequestChangeOut
from app.core.responses import success_response

router = APIRouter(prefix="/request-changes", tags=["Request Changes"])


@router.post("/", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
def create_request_change(payload: RequestChangeCreate, db: Session = Depends(get_db)):
    """Create a new human-in-the-loop request change log."""
    repo = RequestChangeRepository(db)
    
    # Coerce project_id to UUID
    proj_id = payload.project_id
    if not isinstance(proj_id, uuid.UUID):
        try:
            proj_id = uuid.UUID(str(proj_id))
        except ValueError:
            proj_id = uuid.uuid5(uuid.NAMESPACE_DNS, str(proj_id))

    bp_id = payload.blueprint_id
    if bp_id and not isinstance(bp_id, uuid.UUID):
        try:
            bp_id = uuid.UUID(str(bp_id))
        except ValueError:
            bp_id = uuid.uuid5(uuid.NAMESPACE_DNS, str(bp_id))

    # Try to fetch original value to preserve versioning audit trail
    original_val = None
    if payload.location_type.lower() == "epic" and payload.target_id:
        epic = db.query(EpicModel).filter(EpicModel.project_id == proj_id, EpicModel.epic_key == payload.target_id).first()
        if epic and payload.field_name:
            original_val = getattr(epic, payload.field_name, None)
    elif payload.location_type.lower() == "user story" and payload.target_id:
        story = db.query(StoryModel).filter(StoryModel.project_id == proj_id, StoryModel.story_key == payload.target_id).first()
        if story and payload.field_name:
            if payload.field_name == "title":
                original_val = story.story_title
            elif payload.field_name == "description":
                original_val = story.story_description
            else:
                original_val = getattr(story, payload.field_name, None)

    # Insert request change
    insert_data = payload.model_dump()
    insert_data["project_id"] = proj_id
    insert_data["blueprint_id"] = bp_id
    insert_data["original_value"] = original_val
    rc = repo.create(insert_data)
    db.commit()

    return success_response(
        data={
            "request_change_id": str(rc.request_change_id),
            "status": rc.status,
            "location_type": rc.location_type,
            "target_id": rc.target_id,
            "requested_change": rc.requested_change,
        },
        message="Request change log recorded successfully."
    )


@router.get("/", response_model=Dict[str, Any])
def list_request_changes(
    project_id: str = Query(..., description="Project UUID context filter"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Retrieve all request changes logged for a project."""
    repo = RequestChangeRepository(db)
    try:
        proj_uuid = uuid.UUID(project_id)
    except ValueError:
        return success_response(data=[], message="Invalid project ID.")
    records = repo.get_by_project(proj_uuid, skip=skip, limit=limit)
    
    out_list = []
    for r in records:
        out_list.append({
            "request_change_id": str(r.request_change_id),
            "project_id": str(r.project_id),
            "blueprint_id": str(r.blueprint_id) if r.blueprint_id else None,
            "blueprint_version": r.blueprint_version,
            "location_type": r.location_type,
            "target_id": r.target_id,
            "target_path": r.target_path,
            "field_name": r.field_name,
            "original_value": r.original_value,
            "requested_change": r.requested_change,
            "modified_prompt": r.modified_prompt,
            "modified_value": r.modified_value,
            "status": r.status,
            "created_by": r.created_by,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "updated_at": r.updated_at.isoformat() if r.updated_at else None,
        })

    return success_response(
        data=out_list,
        message="Request changes retrieved successfully."
    )


@router.post("/{request_change_id}/apply", response_model=Dict[str, Any])
def apply_request_change(request_change_id: uuid.UUID, db: Session = Depends(get_db)):
    """Apply the request change dynamically to the targeted database element/file."""
    repo = RequestChangeRepository(db)
    rc = repo.get(request_change_id)
    if not rc:
        raise HTTPException(status_code=404, detail="Request change not found")

    rc.status = "PROCESSING"
    db.commit()

    try:
        # Generate modification prompt
        rc.modified_prompt = f"System modification directive: Change target '{rc.target_id or rc.target_path}' field '{rc.field_name}' to '{rc.requested_change}'."
        
        # Apply change to database models dynamically
        if rc.location_type.lower() == "epic" and rc.target_id:
            epic = db.query(EpicModel).filter(EpicModel.project_id == rc.project_id, EpicModel.epic_key == rc.target_id).first()
            if epic and rc.field_name:
                setattr(epic, rc.field_name, rc.requested_change)
                rc.modified_value = rc.requested_change
                
                # Fetch related blueprint and bump version
                if epic.blueprint:
                    old_v = epic.blueprint.version
                    epic.blueprint.version = old_v + 1
                    rc.blueprint_id = epic.blueprint.blueprint_id
                    rc.blueprint_version = old_v + 1
                    
        elif rc.location_type.lower() in ("user story", "story") and rc.target_id:
            story = db.query(StoryModel).filter(StoryModel.project_id == rc.project_id, StoryModel.story_key == rc.target_id).first()
            if story and rc.field_name:
                if rc.field_name == "title":
                    story.story_title = rc.requested_change
                elif rc.field_name == "description":
                    story.story_description = rc.requested_change
                else:
                    setattr(story, rc.field_name, rc.requested_change)
                rc.modified_value = rc.requested_change

            # Update story.json inside workspace sandbox if present
            s_id = rc.target_id.upper()
            from pathlib import Path
            import json
            ws_path = Path(__file__).resolve().parent.parent.parent / "workspace" / s_id / "story.json"
            if ws_path.exists():
                try:
                    with open(ws_path, "r", encoding="utf-8") as f:
                        s_data = json.load(f)
                    if rc.field_name:
                        s_data[rc.field_name] = rc.requested_change
                    s_data["status"] = "REFINED"
                    with open(ws_path, "w", encoding="utf-8") as f:
                        json.dump(s_data, f, indent=2)
                except Exception as ex:
                    pass

        elif rc.location_type.lower() == "blueprint":
            bp = db.query(BlueprintModel).filter(BlueprintModel.project_id == rc.project_id).order_by(BlueprintModel.version.desc()).first()
            if bp:
                old_v = bp.version
                bp.version = old_v + 1
                rc.blueprint_id = bp.blueprint_id
                rc.blueprint_version = old_v + 1
                
                # Append feedback refinement info
                if not bp.architecture:
                    bp.architecture = ""
                bp.architecture += f" (Refined: {rc.requested_change})"
                rc.modified_value = bp.architecture

        rc.status = "APPLIED"
        rc.updated_at = datetime.now(timezone.utc)
        db.commit()

        return success_response(
            data={
                "request_change_id": str(rc.request_change_id),
                "status": rc.status,
                "applied_value": rc.modified_value,
                "version_bumped": rc.blueprint_version
            },
            message="Request change applied and database records updated successfully."
        )
    except Exception as e:
        db.rollback()
        rc.status = "FAILED"
        rc.updated_at = datetime.now(timezone.utc)
        db.commit()
        raise HTTPException(status_code=500, detail=f"Failed to apply requested changes: {e}")
