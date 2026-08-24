"""FastAPI application entry point for the integrated TodoApp backend service."""

from fastapi import FastAPI, APIRouter, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Any
import os

try:
    from .task_service import (
        get_all_tasks,
        get_task_by_id,
        create_new_task,
        update_task,
        complete_task,
        delete_task,
        search_tasks_by_query,
        filter_tasks_by_status,
        get_dashboard_summary,
        register_user,
        authenticate_user
    )
except ImportError:
    from task_service import (
        get_all_tasks,
        get_task_by_id,
        create_new_task,
        update_task,
        complete_task,
        delete_task,
        search_tasks_by_query,
        filter_tasks_by_status,
        get_dashboard_summary,
        register_user,
        authenticate_user
    )

app = FastAPI(title="TodoApp Integrated API", version="1.0.0")

# Enable CORS for local Vite dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health & Status endpoints required by IntegratedProjectRunner
@app.get("/health")
def health_check():
    return {"status": "ok", "service": "TodoApp Backend API", "version": "1.0.0"}

@app.get("/status")
def status_check():
    return {
        "status": "running",
        "service": "TodoApp Backend",
        "tasks_count": len(get_all_tasks())
    }

# ── Auth Endpoints ──
class LoginReq(BaseModel):
    email: str
    password: str

class RegisterReq(BaseModel):
    name: str
    email: str
    password: str

@app.post("/api/v1/auth/login")
def login(req: LoginReq):
    token = authenticate_user(req.email, req.password)
    if not token:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return {"access_token": token, "token_type": "bearer", "user": {"email": req.email, "name": req.email.split("@")[0].title()}}

@app.post("/api/v1/auth/register", status_code=status.HTTP_201_CREATED)
def register(req: RegisterReq):
    res = register_user(req.name, req.email, req.password)
    if res.get("status") == "error":
        raise HTTPException(status_code=400, detail=res["message"])
    return res

# ── Task Endpoints ──
class TaskCreateReq(BaseModel):
    title: str
    description: Optional[str] = ""
    due_date: Optional[str] = ""
    priority: Optional[str] = "Medium"

class TaskUpdateReq(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[str] = None
    priority: Optional[str] = None

class TaskCompleteReq(BaseModel):
    completed: bool = True

@app.get("/api/v1/tasks")
def list_tasks(status: Optional[str] = None, search: Optional[str] = None):
    if search:
        return search_tasks_by_query(search)
    if status:
        return filter_tasks_by_status(status)
    return get_all_tasks()

@app.post("/api/v1/tasks", status_code=status.HTTP_201_CREATED)
def create_task(req: TaskCreateReq):
    return create_new_task(req.title, req.description, req.due_date, req.priority)

@app.get("/api/v1/tasks/{task_id}")
def get_task(task_id: str):
    task = get_task_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@app.put("/api/v1/tasks/{task_id}")
def edit_task(task_id: str, req: TaskUpdateReq):
    task = update_task(task_id, req.title, req.description, req.due_date, req.priority)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@app.patch("/api/v1/tasks/{task_id}/complete")
def toggle_complete(task_id: str, req: TaskCompleteReq):
    task = complete_task(task_id, req.completed)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@app.delete("/api/v1/tasks/{task_id}")
def remove_task(task_id: str):
    success = delete_task(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Task deleted successfully", "id": task_id}

@app.get("/api/v1/dashboard")
def dashboard():
    return get_dashboard_summary()

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", "8010"))
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port, reload=True)
