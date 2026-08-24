from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List
from sqlalchemy import create_engine, Column, Integer, String, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

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
    status = Column(String, index=True)

Base.metadata.create_all(bind=engine)

# Pydantic models
class TaskBase(BaseModel):
    title: str
    status: str

class TaskUpdate(BaseModel):
    title: str | None
    status: str | None

# FastAPI app
app = FastAPI()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Get all tasks
@app.get("/tasks/")
def read_tasks(db: Session = Depends(get_db)):
    return db.query(Task).all()

# Get task by id
@app.get("/tasks/{task_id}")
def read_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

# Create task
@app.post("/tasks/")
def create_task(task: TaskBase, db: Session = Depends(get_db)):
    db_task = Task(title=task.title, status=task.status)
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

# Update task
@app.put("/tasks/{task_id}")
def update_task(task_id: int, task: TaskUpdate, db: Session = Depends(get_db)):
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.title:
        db_task.title = task.title
    if task.status:
        db_task.status = task.status
    db.commit()
    db.refresh(db_task)
    return db_task

# Delete task
@app.delete("/tasks/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()
    return {"message": "Task deleted"}