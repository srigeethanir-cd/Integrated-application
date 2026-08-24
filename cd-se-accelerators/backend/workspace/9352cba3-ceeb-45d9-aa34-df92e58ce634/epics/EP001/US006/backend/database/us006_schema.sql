python
# database/models.py
from sqlalchemy import Column, Integer, String, Enum, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class Task(Base):
    __tablename__ = 'tasks'
    id = Column(Integer, primary_key=True)
    title = Column(String)
    description = Column(String)
    status = Column(Enum('pending', 'completed', name='task_status'))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

# database/repository.py
from database.models import Session, Task

class TaskRepository:
    def __init__(self, session):
        self.session = session

    def mark_task_complete(self, task_id):
        task = self.session.query(Task).filter_by(id=task_id).first()
        if task:
            task.status = 'completed'
            self.session.commit()
            return task
        return None

# main.py
from fastapi import FastAPI, HTTPException
from database.repository import TaskRepository
from database.models import Session

app = FastAPI()

@app.put("/tasks/{task_id}/complete")
async def mark_task_complete(task_id: int):
    session = Session()
    task_repository = TaskRepository(session)
    task = task_repository.mark_task_complete(task_id)
    if task:
        return {"message": "Task marked as completed"}
    else:
        raise HTTPException(status_code=404, detail="Task not found")

# schema.py
from pydantic import BaseModel

class TaskSchema(BaseModel):
    id: int
    title: str
    description: str
    status: str

# react component