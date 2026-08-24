python
# database.py
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Create a database engine
engine = create_engine('sqlite:///tasks.db')

# Create a configured "Session" class
Session = sessionmaker(bind=engine)

# Create a base class for declarative class definitions
Base = declarative_base()

class Task(Base):
    """Task model"""
    __tablename__ = 'tasks'
    id = Column(Integer, primary_key=True)
    title = Column(String)

    def __repr__(self):
        return f'Task(id={self.id}, title={self.title})'

# Create all tables in the engine
Base.metadata.create_all(engine)

# task_service.py
from database import Session, Task

class TaskService:
    """Task service"""
    def create_task(self, title: str):
        """Create a new task"""
        session = Session()
        task = Task(title=title)
        session.add(task)
        session.commit()
        session.close()
        return task

# main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from task_service import TaskService

app = FastAPI()
task_service = TaskService()

class TaskRequest(BaseModel):
    title: str

@app.post("/tasks/")
async def create_task(task_request: TaskRequest):
    try:
        task = task_service.create_task(task_request.title)
        return {"id": task.id, "title": task.title}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))