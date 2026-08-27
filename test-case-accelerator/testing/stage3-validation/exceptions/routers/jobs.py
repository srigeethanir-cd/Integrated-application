from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from schemas import JobCreate, JobOut
from services.jobs import DependencyUnavailableError, JobConflictError, JobNotFoundError, create_job, transition
router = APIRouter(prefix="/jobs")
def require_dependency(x_dependency_state: str = Header(default="up")):
    if x_dependency_state != "up":
        raise DependencyUnavailableError("dependency unavailable")
@router.post("/", response_model=JobOut, status_code=201, dependencies=[Depends(require_dependency)])
def create(payload: JobCreate, db: Session = Depends(get_db)):
    return create_job(db, payload)
@router.put("/{job_id}", response_model=JobOut)
def update(job_id: int, state: str, db: Session = Depends(get_db)):
    try:
        return transition(db, job_id, state)
    except JobNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except JobConflictError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
