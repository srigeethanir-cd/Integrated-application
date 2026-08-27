"""Component API routes."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.repository.component_repository import ComponentRepository
from app.schemas import ComponentCreate, ComponentOut, ComponentUpdate

router = APIRouter(prefix="/components", tags=["Components"])


@router.post("/", response_model=ComponentOut, status_code=status.HTTP_201_CREATED)
def create_component(payload: ComponentCreate, db: Session = Depends(get_db)):
    """Create a new component."""
    repo = ComponentRepository(db)
    return repo.create(payload.model_dump())


@router.get("/", response_model=list[ComponentOut])
def list_components(
    project_id: uuid.UUID | None = Query(None, description="Filter by project"),
    component_type: str | None = Query(None, alias="type", description="Filter by type"),
    agent: str | None = Query(None, description="Filter by creating agent"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """List components with optional filters."""
    repo = ComponentRepository(db)
    if project_id:
        return repo.get_by_project(project_id, skip=skip, limit=limit)
    if component_type:
        return repo.get_by_type(component_type, skip=skip, limit=limit)
    if agent:
        return repo.get_by_agent(agent, skip=skip, limit=limit)
    return repo.get_all(skip=skip, limit=limit)


@router.get("/{component_id}", response_model=ComponentOut)
def get_component(component_id: uuid.UUID, db: Session = Depends(get_db)):
    """Get a single component by ID."""
    repo = ComponentRepository(db)
    component = repo.get(component_id)
    if not component:
        raise HTTPException(status_code=404, detail="Component not found")
    return component


@router.patch("/{component_id}", response_model=ComponentOut)
def update_component(component_id: uuid.UUID, payload: ComponentUpdate, db: Session = Depends(get_db)):
    """Update a component (partial)."""
    repo = ComponentRepository(db)
    db_obj = repo.get(component_id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Component not found")
    return repo.update(db_obj, payload.model_dump(exclude_unset=True))


@router.delete("/{component_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_component(component_id: uuid.UUID, db: Session = Depends(get_db)):
    """Delete a component."""
    repo = ComponentRepository(db)
    if not repo.delete(component_id):
        raise HTTPException(status_code=404, detail="Component not found")
