from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Boolean

# Database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///tasks.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Task model
class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String, index=True)
    completed = Column(Boolean, default=False)

Base.metadata.create_all(bind=engine)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Request body model
class TaskUpdate(BaseModel):
    id: int
    completed: bool

# Router
router = APIRouter()

@router.put("/tasks/{task_id}/complete", response_class=JSONResponse)
def mark_task_complete(task_id: int, task_update: TaskUpdate, db = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    if task_update.completed:
        task.completed = True
        db.commit()
        return {"message": "Task marked as completed"}
    else:
        raise HTTPException(status_code=400, detail="Invalid request body")