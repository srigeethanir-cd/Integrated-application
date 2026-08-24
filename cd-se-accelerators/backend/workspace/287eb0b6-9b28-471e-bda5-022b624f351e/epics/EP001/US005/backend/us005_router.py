from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

class Task(BaseModel):
    id: int
    title: str
    status: str

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None

# Mock task data
tasks = [
    {"id": 1, "title": "Task 1", "status": "pending"},
    {"id": 2, "title": "Task 2", "status": "in_progress"},
]

@app.put("/tasks/{task_id}")
async def update_task(task_id: int, task_update: TaskUpdate):
    for task in tasks:
        if task["id"] == task_id:
            if task_update.title:
                task["title"] = task_update.title
            if task_update.status:
                task["status"] = task_update.status
            return task
    raise HTTPException(status_code=404, detail="Task not found")

@app.get("/tasks/{task_id}")
async def get_task(task_id: int):
    for task in tasks:
        if task["id"] == task_id:
            return task
    raise HTTPException(status_code=404, detail="Task not found")