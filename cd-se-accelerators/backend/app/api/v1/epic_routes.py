"""Epic API routes."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.repository.epic_repository import EpicRepository
from app.schemas import EpicCreate, EpicOut, EpicUpdate

router = APIRouter(prefix="/epics", tags=["Epics"])


@router.post("/", response_model=EpicOut, status_code=status.HTTP_201_CREATED)
def create_epic(payload: EpicCreate, db: Session = Depends(get_db)):
    """Create a new epic."""
    repo = EpicRepository(db)
    return repo.create(payload.model_dump())


@router.get("/", response_model=list[EpicOut])
def list_epics(
    project_id: uuid.UUID | None = Query(None, description="Filter by project"),
    blueprint_id: uuid.UUID | None = Query(None, description="Filter by blueprint"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """List epics, optionally filtered by project or blueprint."""
    repo = EpicRepository(db)
    if project_id:
        return repo.get_by_project(project_id, skip=skip, limit=limit)
    if blueprint_id:
        return repo.get_by_blueprint(blueprint_id, skip=skip, limit=limit)
    return repo.get_all(skip=skip, limit=limit)


@router.get("/{epic_id}", response_model=EpicOut)
def get_epic(epic_id: uuid.UUID, db: Session = Depends(get_db)):
    """Get a single epic by ID."""
    repo = EpicRepository(db)
    epic = repo.get(epic_id)
    if not epic:
        raise HTTPException(status_code=404, detail="Epic not found")
    return epic


@router.patch("/{epic_id}", response_model=EpicOut)
def update_epic(epic_id: uuid.UUID, payload: EpicUpdate, db: Session = Depends(get_db)):
    """Update an epic (partial)."""
    repo = EpicRepository(db)
    db_obj = repo.get(epic_id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Epic not found")
    return repo.update(db_obj, payload.model_dump(exclude_unset=True))


@router.delete("/{epic_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_epic(epic_id: uuid.UUID, db: Session = Depends(get_db)):
    """Delete an epic and its stories."""
    repo = EpicRepository(db)
    if not repo.delete(epic_id):
        raise HTTPException(status_code=404, detail="Epic not found")
