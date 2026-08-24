from fastapi import APIRouter, status
from .task_service import delete_task

router = APIRouter(prefix="/api/v1/tasks", tags=["Tasks"])

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_task(task_id: str):
    delete_task(task_id)
    return None
