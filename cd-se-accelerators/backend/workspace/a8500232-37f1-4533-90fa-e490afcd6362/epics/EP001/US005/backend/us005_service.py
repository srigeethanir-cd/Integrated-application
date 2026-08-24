from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List

app = FastAPI()

# Define the Task model
class Task(BaseModel):
    id: int
    title: str
    status: str

# In-memory task storage (replace with a database in a real application)
tasks = [
    {"id": 1, "title": "Task 1", "status": "pending"},
    {"id": 2, "title": "Task 2", "status": "in_progress"},
]

# Define the endpoint to update a task
@app.put("/tasks/{task_id}")
async def update_task(task_id: int, task: Task):
    # Find the task to update
    task_to_update = next((t for t in tasks if t["id"] == task_id), None)
    
    # Check if the task exists
    if task_to_update is None:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Update the task
    task_to_update["title"] = task.title
    task_to_update["status"] = task.status
    
    # Return the updated task
    return task_to_update

# Define the endpoint to get all tasks
@app.get("/tasks")
async def get_tasks():
    return tasks

# Define the endpoint to get a task by id
@app.get("/tasks/{task_id}")
async def get_task(task_id: int):
    task = next((t for t in tasks if t["id"] == task_id), None)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task