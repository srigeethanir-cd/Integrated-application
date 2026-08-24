from pydantic import BaseModel
from enum import Enum

class TaskStatus(str, Enum):
    todo = "todo"
    in_progress = "in_progress"
    done = "done"

class Task(BaseModel):
    id: int
    title: str
    status: TaskStatus

class TaskUpdate(BaseModel):
    title: str | None
    status: TaskStatus | None