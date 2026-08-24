from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

app = FastAPI()

# Define the Task model
class Task(BaseModel):
    id: int
    title: str
    description: str

# In-memory task storage (replace with a database in a real application)
tasks = [
    Task(id=1, title="Task 1", description="This is task 1"),
    Task(id=2, title="Task 2", description="This is task 2"),
    Task(id=3, title="Task 3", description="This is task 3"),
]

# Define the Dashboard model
class Dashboard(BaseModel):
    tasks: List[Task]
    task_count: int

# Create a route to view the dashboard
@app.get("/dashboard", response_model=Dashboard)
async def view_dashboard():
    try:
        # Retrieve tasks from storage
        tasks_list = tasks
        
        # Create a dashboard object
        dashboard = Dashboard(tasks=tasks_list, task_count=len(tasks_list))
        
        # Return the dashboard
        return dashboard
    
    except Exception as e:
        # Handle any exceptions
        raise HTTPException(status_code=500, detail=str(e))

# Create a route to create a new task
@app.post("/tasks", response_model=Task)
async def create_task(task: Task):
    try:
        # Add the new task to storage
        tasks.append(task)
        
        # Return the created task
        return task
    
    except Exception as e:
        # Handle any exceptions
        raise HTTPException(status_code=500, detail=str(e))