from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
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
    description = Column(String, index=True)

Base.metadata.create_all(bind=engine)

# Pydantic task model
class TaskModel(BaseModel):
    id: int
    title: str
    description: str

# FastAPI app
app = FastAPI()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Delete task endpoint
@app.delete("/tasks/{task_id}", response_model=None)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()
    return JSONResponse(status_code=200, content={"message": "Task deleted successfully"})

# Create task endpoint for testing
@app.post("/tasks", response_model=TaskModel)
def create_task(task: TaskModel, db: Session = Depends(get_db)):
    db_task = Task(title=task.title, description=task.description)
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

# Get tasks endpoint for testing
@app.get("/tasks", response_model=list[TaskModel])
def get_tasks(db: Session = Depends(get_db)):
    tasks = db.query(Task).all()
    return tasks