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

# Create a task endpoint
@app.post("/tasks/")
async def create_task(task: Task):
    # Generate a unique ID for the task if not provided
    if task.id is None:
        task.id = uuid4()
    
    # Set the created_at timestamp
    task.created_at = datetime.now()
    
    # Save the task to the in-memory storage
    tasks.append(task.dict())
    
    # Return the saved task
    return task

# Error handling for invalid task title
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return {"error": exc.detail}

# Example usage:
# curl -X POST -H "Content-Type: application/json" -d '{"title": "New Task"}' http://localhost:8000/tasks/