from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime

app = FastAPI()

# Define the Task model
class Task(BaseModel):
    id: Optional[UUID] = None
    title: str
    created_at: Optional[datetime] = None

# In-memory task storage (replace with a database in a real application)
tasks = []

# Create a task
@app.post("/tasks/")
async def create_task(task: Task):
    task.id = uuid4()
    task.created_at = datetime.now()
    tasks.append(task)
    return {"message": "Task is saved successfully", "task": task}

# Error handling for invalid task title
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return {"error": exc.detail}

# Test the create task endpoint
@app.get("/tasks/")
async def read_tasks():
    return tasks