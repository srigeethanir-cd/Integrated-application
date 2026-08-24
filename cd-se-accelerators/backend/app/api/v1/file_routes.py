"""File API routes."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.repository.file_repository import FileRepository
from app.schemas import FileCreate, FileOut, FileUpdate

router = APIRouter(prefix="/files", tags=["Files"])


@router.post("/", response_model=FileOut, status_code=status.HTTP_201_CREATED)
def create_file(payload: FileCreate, db: Session = Depends(get_db)):
    """Register a new generated file."""
    repo = FileRepository(db)
    return repo.create(payload.model_dump())


@router.get("/", response_model=list[FileOut])
def list_files(
    component_id: uuid.UUID | None = Query(None, description="Filter by component"),
    story_id: uuid.UUID | None = Query(None, description="Filter by story"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """List files with optional filters."""
    repo = FileRepository(db)
    if component_id:
        return repo.get_by_component(component_id, skip=skip, limit=limit)
    if story_id:
        return repo.get_by_story(story_id, skip=skip, limit=limit)
    return repo.get_all(skip=skip, limit=limit)


@router.get("/{file_id}", response_model=FileOut)
def get_file(file_id: uuid.UUID, db: Session = Depends(get_db)):
    """Get a single file by ID."""
    repo = FileRepository(db)
    file = repo.get(file_id)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    return file


@router.patch("/{file_id}", response_model=FileOut)
def update_file(file_id: uuid.UUID, payload: FileUpdate, db: Session = Depends(get_db)):
    """Update a file record (partial)."""
    repo = FileRepository(db)
    db_obj = repo.get(file_id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="File not found")
    return repo.update(db_obj, payload.model_dump(exclude_unset=True))


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_file(file_id: uuid.UUID, db: Session = Depends(get_db)):
    """Delete a file record."""
    repo = FileRepository(db)
    if not repo.delete(file_id):
        raise HTTPException(status_code=404, detail="File not found")
