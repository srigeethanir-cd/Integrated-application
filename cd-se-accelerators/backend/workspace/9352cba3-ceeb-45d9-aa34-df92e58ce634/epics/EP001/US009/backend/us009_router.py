from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

app = FastAPI()

class Task(BaseModel):
    id: int
    title: str
    status: str

# In-memory task storage for demonstration purposes
tasks = [
    Task(id=1, title="Task 1", status="pending"),
    Task(id=2, title="Task 2", status="completed"),
    Task(id=3, title="Task 3", status="pending"),
]

@app.get("/tasks/")
async def read_tasks(status: str = None):
    if status:
        return [task for task in tasks if task.status == status]
    return tasks

@app.get("/tasks/{task_id}")
async def read_task(task_id: int):
    for task in tasks:
        if task.id == task_id:
            return task
    raise HTTPException(status_code=404, detail="Task not found")

@app.post("/tasks/")
async def create_task(task: Task):
    tasks.append(task)
    return task

@app.put("/tasks/{task_id}")
async def update_task(task_id: int, task: Task):
    for i, t in enumerate(tasks):
        if t.id == task_id:
            tasks[i] = task
            return task
    raise HTTPException(status_code=404, detail="Task not found")

@app.delete("/tasks/{task_id}")
async def delete_task(task_id: int):
    for i, task in enumerate(tasks):
        if task.id == task_id:
            del tasks[i]
            return {"message": "Task deleted"}
    raise HTTPException(status_code=404, detail="Task not found")