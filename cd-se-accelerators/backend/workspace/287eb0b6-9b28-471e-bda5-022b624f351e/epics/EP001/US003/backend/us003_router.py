from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class Task(BaseModel):
    id: int
    title: str
    description: str

# In-memory task storage for demonstration purposes
tasks = [
    Task(id=1, title="Task 1", description="This is task 1"),
    Task(id=2, title="Task 2", description="This is task 2"),
    Task(id=3, title="Task 3", description="This is task 3"),
]

@app.get("/tasks/")
async def read_tasks():
    return tasks

@app.get("/tasks/count")
async def read_task_count():
    return {"task_count": len(tasks)}