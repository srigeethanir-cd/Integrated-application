from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class Task(BaseModel):
    title: str

tasks = []

@app.post("/tasks/")
async def create_task(task: Task):
    tasks.append(task)
    return {"message": "Task is saved successfully"}

@app.get("/tasks/")
async def read_tasks():
    return tasks