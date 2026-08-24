from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from uuid import uuid4

app = FastAPI()

class Task(BaseModel):
    id: Optional[str]
    title: str

class TaskResponse(BaseModel):
    id: str
    title: str

tasks = {}

@app.post("/tasks", response_model=TaskResponse)
async def create_task(task: Task):
    if not task.title:
        raise HTTPException(status_code=400, detail="Task title is required")
    
    task_id = str(uuid4())
    tasks[task_id] = task
    
    return TaskResponse(id=task_id, title=task.title)