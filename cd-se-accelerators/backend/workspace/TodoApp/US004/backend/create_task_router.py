from fastapi import APIRouter, status
from pydantic import BaseModel
from typing import Optional
from .task_service import create_new_task

router = APIRouter(prefix="/api/v1/tasks", tags=["Tasks"])

class CreateTaskRequest(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: str

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_task(req: CreateTaskRequest):
    return create_new_task(req.title, req.description, req.due_date)
