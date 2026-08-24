"""In-memory task store and CRUD operations for TodoApp integrated backend."""

import uuid
from typing import Dict, List, Optional
from datetime import datetime

# In-memory database of tasks
_TASKS: Dict[str, dict] = {
    "task-001": {
        "id": "task-001",
        "title": "Setup development environment",
        "description": "Install Python, Node.js, and dependencies for TodoApp",
        "due_date": "2026-08-05",
        "priority": "High",
        "status": "Completed",
        "completed": True,
        "created_at": "2026-08-01T10:00:00Z"
    },
    "task-002": {
        "id": "task-002",
        "title": "Design user authentication flow",
        "description": "Create wireframes and specs for registration and login",
        "due_date": "2026-08-06",
        "priority": "Medium",
        "status": "In Progress",
        "completed": False,
        "created_at": "2026-08-01T11:30:00Z"
    },
    "task-003": {
        "id": "task-003",
        "title": "Review story implementation specs",
        "description": "Validate US001 to US010 blueprint mappings",
        "due_date": "2026-08-07",
        "priority": "High",
        "status": "Pending",
        "completed": False,
        "created_at": "2026-08-02T09:00:00Z"
    }
}

# User registration store
_USERS: Dict[str, dict] = {
    "user@todoapp.com": {
        "id": "usr_001",
        "name": "Demo User",
        "email": "user@todoapp.com",
        "password": "password123"
    }
}


def get_all_tasks() -> List[dict]:
    return list(_TASKS.values())


def get_task_by_id(task_id: str) -> Optional[dict]:
    return _TASKS.get(task_id)


def create_new_task(title: str, description: Optional[str] = "", due_date: Optional[str] = "", priority: str = "Medium") -> dict:
    task_id = f"task-{uuid.uuid4().hex[:6]}"
    now = datetime.utcnow().isoformat() + "Z"
    task = {
        "id": task_id,
        "title": title,
        "description": description or "",
        "due_date": due_date or datetime.now().strftime("%Y-%m-%d"),
        "priority": priority or "Medium",
        "status": "Pending",
        "completed": False,
        "created_at": now
    }
    _TASKS[task_id] = task
    return task


def update_task(task_id: str, title: Optional[str] = None, description: Optional[str] = None, due_date: Optional[str] = None, priority: Optional[str] = None) -> Optional[dict]:
    task = _TASKS.get(task_id)
    if not task:
        return None
    if title is not None:
        task["title"] = title
    if description is not None:
        task["description"] = description
    if due_date is not None:
        task["due_date"] = due_date
    if priority is not None:
        task["priority"] = priority
    return task


def complete_task(task_id: str, is_completed: bool = True) -> Optional[dict]:
    task = _TASKS.get(task_id)
    if not task:
        return None
    task["completed"] = is_completed
    task["status"] = "Completed" if is_completed else "Pending"
    return task


def delete_task(task_id: str) -> bool:
    if task_id in _TASKS:
        del _TASKS[task_id]
        return True
    return False


def search_tasks_by_query(query: str) -> List[dict]:
    if not query or not query.strip():
        return get_all_tasks()
    q = query.lower().strip()
    return [
        t for t in _TASKS.values()
        if q in t["title"].lower() or q in t.get("description", "").lower()
    ]


def filter_tasks_by_status(status: str) -> List[dict]:
    if not status or status.lower() in ("all", "any"):
        return get_all_tasks()
    st = status.lower()
    if st == "completed":
        return [t for t in _TASKS.values() if t["completed"] or t["status"].lower() == "completed"]
    elif st == "pending" or st == "active":
        return [t for t in _TASKS.values() if not t["completed"]]
    elif st == "in progress":
        return [t for t in _TASKS.values() if t["status"].lower() == "in progress"]
    return [t for t in _TASKS.values() if t["status"].lower() == st]


def get_dashboard_summary() -> dict:
    tasks = list(_TASKS.values())
    total = len(tasks)
    completed = sum(1 for t in tasks if t["completed"])
    in_progress = sum(1 for t in tasks if t["status"].lower() == "in progress")
    pending = total - completed - in_progress
    overdue = sum(1 for t in tasks if not t["completed"] and t.get("due_date", "") and t["due_date"] < datetime.now().strftime("%Y-%m-%d"))

    return {
        "total": total,
        "completed": completed,
        "in_progress": in_progress,
        "pending": pending,
        "overdue": overdue,
        "recent_tasks": tasks[-5:] if tasks else []
    }


def register_user(name: str, email: str, password: str) -> dict:
    if email in _USERS:
        return {"status": "error", "message": "Email already registered", "user_id": _USERS[email]["id"]}
    user_id = f"usr_{uuid.uuid4().hex[:6]}"
    user = {"id": user_id, "name": name, "email": email, "password": password}
    _USERS[email] = user
    return {"status": "success", "message": f"User {email} registered successfully", "user_id": user_id}


def authenticate_user(email: str, password: str) -> Optional[str]:
    user = _USERS.get(email)
    if user and user["password"] == password:
        return f"jwt_token_{user['id']}"
    # Fallback demo login
    if email and len(password) >= 4:
        return f"jwt_token_demo_{email}"
    return None
