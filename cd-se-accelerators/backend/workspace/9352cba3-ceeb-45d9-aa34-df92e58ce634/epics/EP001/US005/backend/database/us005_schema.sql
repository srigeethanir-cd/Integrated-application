python
# database.py
from sqlalchemy import create_engine, Column, Integer, String, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Create a database engine
engine = create_engine('postgresql://user:password@host:port/dbname')

# Create a configured "Session" class
Session = sessionmaker(bind=engine)

# Create a base class for declarative class definitions
Base = declarative_base()

class Task(Base):
    __tablename__ = 'tasks'
    id = Column(Integer, primary_key=True)
    title = Column(String)
    status = Column(Enum('todo', 'in_progress', 'done'))

    def __repr__(self):
        return f'Task(id={self.id}, title={self.title}, status={self.status})'

# Create all tables in the engine
Base.metadata.create_all(engine)

# task_service.py
from database import Session, Task

class TaskService:
    def __init__(self):
        self.session = Session()

    def get_task(self, task_id):
        return self.session.query(Task).filter_by(id=task_id).first()

    def update_task(self, task_id, title=None, status=None):
        task = self.get_task(task_id)
        if task:
            if title:
                task.title = title
            if status:
                task.status = status
            self.session.commit()
        return task

# main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from task_service import TaskService

app = FastAPI()

class TaskRequest(BaseModel):
    title: str | None
    status: str | None

task_service = TaskService()

@app.put("/tasks/{task_id}")
async def update_task(task_id: int, task_request: TaskRequest):
    task = task_service.update_task(task_id, task_request.title, task_request.status)
    if task:
        return {"id": task.id, "title": task.title, "status": task.status}
    else:
        raise HTTPException(status_code=404, detail="Task not found")