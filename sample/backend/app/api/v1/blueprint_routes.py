"""Blueprint API routes."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.repository.blueprint_repository import BlueprintRepository
from app.schemas import BlueprintCreate, BlueprintOut, BlueprintUpdate

router = APIRouter(prefix="/blueprints", tags=["Blueprints"])


@router.post("/", response_model=BlueprintOut, status_code=status.HTTP_201_CREATED)
def create_blueprint(payload: BlueprintCreate, db: Session = Depends(get_db)):
    """Create a new blueprint version."""
    repo = BlueprintRepository(db)
    return repo.create(payload.model_dump())


@router.get("/", response_model=list[BlueprintOut])
def list_blueprints(
    project_id: str | None = Query(None, description="Filter by project"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """List blueprints, optionally filtered by project."""
    repo = BlueprintRepository(db)
    if project_id:
        try:
            proj_uuid = uuid.UUID(project_id)
            return repo.get_by_project(proj_uuid, skip=skip, limit=limit)
        except ValueError:
            return []
    return repo.get_all(skip=skip, limit=limit)


@router.get("/{blueprint_id}", response_model=BlueprintOut)
def get_blueprint(blueprint_id: uuid.UUID, db: Session = Depends(get_db)):
    """Get a single blueprint by ID."""
    repo = BlueprintRepository(db)
    bp = repo.get(blueprint_id)
    if not bp:
        raise HTTPException(status_code=404, detail="Blueprint not found")
    return bp


@router.patch("/{blueprint_id}", response_model=BlueprintOut)
def update_blueprint(blueprint_id: uuid.UUID, payload: BlueprintUpdate, db: Session = Depends(get_db)):
    """Update a blueprint (partial)."""
    repo = BlueprintRepository(db)
    db_obj = repo.get(blueprint_id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Blueprint not found")
    return repo.update(db_obj, payload.model_dump(exclude_unset=True))


@router.post("/generate")
def generate_blueprint(payload: dict):
    """Generate complete project blueprint using Agent-1."""
    from agents.agent1_blueprint import Agent1Blueprint
    agent1 = Agent1Blueprint()
    
    stories = payload.get("user_stories") or payload.get("stories") or []
    tech_stack = payload.get("tech_stack", "Python FastAPI / React TypeScript")
    project_name = payload.get("project_name") or "Generated Application"
    project_description = payload.get("project_description", "")
    ui_metadata = payload.get("ui_metadata")
    wireframe_images = payload.get("wireframe_images")
    workspace_metadata = payload.get("workspace_metadata")
    project_id = payload.get("project_id") or str(uuid.uuid4())

    res = agent1.process(
        stories=stories,
        tech_stack=tech_stack,
        ui_metadata=ui_metadata,
        project_id=project_id,
        project_name=project_name,
        project_description=project_description,
        wireframe_images=wireframe_images,
        workspace_metadata=workspace_metadata,
    )
    return res


@router.post("/approve")
@router.post("/approve-blueprint")
def approve_blueprint(
    payload: dict,
    project_id: str | None = Query(None, description="Project ID"),
    db: Session = Depends(get_db)
):
    """Approve or record comments for an architecture blueprint."""
    approved = payload.get("approved", True)
    comments = payload.get("comments", "")
    p_id = project_id or payload.get("project_id")
    
    # Check if blueprint repository has record, else build synthetic approval response
    repo = BlueprintRepository(db)
    blueprints = []
    try:
        if p_id:
            val_uuid = uuid.UUID(p_id)
            blueprints = repo.get_by_project(val_uuid)
    except ValueError:
        pass
    
    status_str = "APPROVED" if approved else "REJECTED"
    if blueprints:
        bp = blueprints[0]
        bp.status = status_str
        db.commit()

    return {
        "status": "success",
        "message": f"Blueprint approval updated to {status_str}.",
        "project_id": p_id,
        "approved": approved,
        "comments": comments
    }



@router.delete("/{blueprint_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_blueprint(blueprint_id: uuid.UUID, db: Session = Depends(get_db)):
    """Delete a blueprint."""
    repo = BlueprintRepository(db)
    if not repo.delete(blueprint_id):
        raise HTTPException(status_code=404, detail="Blueprint not found")

