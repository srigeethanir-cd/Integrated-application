python
# database/models.py
from sqlalchemy import Column, Integer, String, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class Task(Base):
    __tablename__ = 'tasks'
    id = Column(Integer, primary_key=True)
    title = Column(String)
    status = Column(Enum('todo', 'in_progress', 'done'))

    def __repr__(self):
        return f'Task(id={self.id}, title={self.title}, status={self.status})'

# database/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base

SQLALCHEMY_DATABASE_URL = 'sqlite:///tasks.db'

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# main.py
from fastapi import FastAPI, Depends
from pydantic import BaseModel
from database import get_db
from database.models import Task

app = FastAPI()

class TaskRequest(BaseModel):
    id: int
    title: str
    status: str

@app.put("/tasks/{task_id}")
def update_task(task_id: int, task_request: TaskRequest, db = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if task:
        task.title = task_request.title
        task.status = task_request.status
        db.commit()
        db.refresh(task)
        return {"message": "Task updated successfully"}
    else:
        return {"message": "Task not found"}

# schema.ts
interface Task {
  id: number;
  title: string;
  status: string;
}

interface TaskRequest {
  id: number;
  title: string;
  status: string;
}

# component.tsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';

interface Props {
  taskId: number;
}

const TaskComponent: React.FC<Props> = ({ taskId }) => {
  const [task, setTask] = useState<Task | null>(null);
  const [title, setTitle] = useState('');
  const [status, setStatus] = useState('');

  useEffect(() => {
    axios.get(`/tasks/${taskId}`)
      .then(response => {
        setTask(response.data);
        setTitle(response.data.title);
        setStatus(response.data.status);
      })
      .catch(error => {
        console.error(error);
      });
  }, [taskId]);

  const handleUpdateTask = () => {
    const taskRequest: TaskRequest = {
      id: taskId,
      title: title,
      status: status
    };
    axios.put(`/tasks/${taskId}`, taskRequest)
      .then(response => {
        console.log(response.data);
      })
      .catch(error => {
        console.error(error);
      });
  };

  return (
    <div>
      <input type="text" value={title} onChange={(e) => setTitle(e.target.value)} />
      <select value={status} onChange={(e) => setStatus(e.target.value)}>
        <option value="todo">To Do</option>
        <option value="in_progress">In Progress</option>
        <option value="done">Done</option>
      </select>
      <button onClick={handleUpdateTask}>Update Task</button>
    </div>
  );
};

export default TaskComponent;