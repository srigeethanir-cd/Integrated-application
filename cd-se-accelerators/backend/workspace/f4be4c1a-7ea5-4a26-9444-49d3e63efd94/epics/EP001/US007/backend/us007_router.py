# tasks.py
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String
from typing import List

# Database configuration
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

Base.metadata.create_all(bind=engine)

# Pydantic task model
class TaskModel(BaseModel):
    id: int
    title: str
    description: str

# Task router
router = APIRouter()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Delete task endpoint
@router.delete("/tasks/{task_id}", response_model=TaskModel)
def delete_task(task_id: int, db: SessionLocal = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()
    return JSONResponse(content={"message": "Task deleted successfully"}, status_code=200)