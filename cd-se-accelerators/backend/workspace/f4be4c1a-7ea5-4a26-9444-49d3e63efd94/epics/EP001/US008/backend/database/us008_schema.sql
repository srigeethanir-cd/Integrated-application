python
# database.py
from fastapi import FastAPI, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List
from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# Define the database connection
SQLALCHEMY_DATABASE_URL = "sqlite:///tasks.db"

# Create a database engine
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Create a session maker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a base class for models
Base = declarative_base()

# Define the Task model
class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True)
    title = Column(String)

# Create the database tables
Base.metadata.create_all(bind=engine)

# Define the Task schema
class TaskSchema(BaseModel):
    id: int
    title: str

# Create a FastAPI app
app = FastAPI()

# Dependency to get a database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create a route to search tasks by title
@app.get("/tasks/search", response_model=List[TaskSchema])
def search_tasks(title: str, db: Session = Depends(get_db)):
    # Search tasks by title in a case-insensitive manner
    tasks = db.query(Task).filter(Task.title.ilike(f"%{title}%")).all()
    return tasks