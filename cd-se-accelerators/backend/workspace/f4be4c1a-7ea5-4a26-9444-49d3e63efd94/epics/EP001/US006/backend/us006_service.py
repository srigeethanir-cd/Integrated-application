from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.exc import IntegrityError

# Database Configuration
SQLALCHEMY_DATABASE_URL = "sqlite:///tasks.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Task Model
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

# Request Body Model
class TaskRequest(BaseModel):
    id: int

# Router
router = APIRouter()

# Mark Task Complete
@router.post("/tasks/complete")
async def mark_task_complete(task_request: TaskRequest, db = Depends(get_db)):
    try:
        task = db.query(Task).filter(Task.id == task_request.id).first()
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")
        task.completed = True
        db.add(task)
        db.commit()
        return JSONResponse(content={"message": "Task marked as completed"}, status_code=200)
    except IntegrityError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))