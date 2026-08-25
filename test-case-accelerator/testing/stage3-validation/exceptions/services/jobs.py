from sqlalchemy.orm import Session
from models import Job
from schemas import JobCreate
class JobNotFoundError(Exception):
    pass
class JobConflictError(Exception):
    pass
class DependencyUnavailableError(Exception):
    pass
def load_job(db: Session, job_id: int) -> Job:
    job = db.get(Job, job_id)
    if job is None:
        raise JobNotFoundError(f"job {job_id} not found")
    return job
def validate_transition(job: Job, state: str) -> None:
    if job.state == "done":
        raise JobConflictError("completed jobs are immutable")
    if state not in {"running", "done"}:
        raise ValueError("invalid state")
def transition(db: Session, job_id: int, state: str) -> Job:
    try:
        job = load_job(db, job_id)
        validate_transition(job, state)
        job.state = state
        db.commit(); db.refresh(job)
        return job
    except (JobNotFoundError, JobConflictError, ValueError):
        db.rollback()
        raise
def create_job(db: Session, payload: JobCreate) -> Job:
    job = Job(name=payload.name); db.add(job); db.commit(); db.refresh(job); return job
