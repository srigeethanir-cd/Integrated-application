from fastapi import FastAPI, HTTPException
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
    Task(id=1, title="Task 1", status="pending"),
    Task(id=2, title="Task 2", status="completed"),
    Task(id=3, title="Task 3", status="pending"),
]

# Define the filter tasks endpoint
@app.get("/tasks/")
async def filter_tasks(status: str = None):
    """
    Filter tasks by status.

    Args:
    - status (str): The status to filter by. Can be "pending" or "completed".

    Returns:
    - A list of tasks that match the filter criteria.
    """
    if status:
        if status not in ["pending", "completed"]:
            raise HTTPException(status_code=400, detail="Invalid status")
        return [task for task in tasks if task.status == status]
    else:
        return tasks

# Define the create task endpoint
@app.post("/tasks/")
async def create_task(task: Task):
    """
    Create a new task.

    Args:
    - task (Task): The task to create.

    Returns:
    - The created task.
    """
    tasks.append(task)
    return task