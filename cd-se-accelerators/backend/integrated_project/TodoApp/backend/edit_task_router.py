from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from .task_service import update_existing_task

router = APIRouter(prefix="/api/v1/tasks", tags=["Tasks"])

class UpdateTaskRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[str] = None

@router.put("/{task_id}")
def edit_task(task_id: str, req: UpdateTaskRequest):
    return update_existing_task(task_id, req.title, req.description, req.due_date)
