from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

app = FastAPI()

class Task(BaseModel):
    id: int
    title: str

# In-memory task list for demonstration purposes
tasks = [
    Task(id=1, title="Task 1"),
    Task(id=2, title="Task 2"),
    Task(id=3, title="Task 3"),
]

@app.get("/tasks/")
async def read_tasks(title: str | None = None):
    if title:
        return [task for task in tasks if title.casefold() in task.title.casefold()]
    return tasks

@app.get("/tasks/{task_id}")
async def read_task(task_id: int):
    for task in tasks:
        if task.id == task_id:
            return task
    raise HTTPException(status_code=404, detail="Task not found")