from fastapi import APIRouter
from .task_service import mark_completed

router = APIRouter(prefix="/api/v1/tasks", tags=["Tasks"])

@router.patch("/{task_id}/complete")
def complete_task(task_id: str):
    return mark_completed(task_id)
