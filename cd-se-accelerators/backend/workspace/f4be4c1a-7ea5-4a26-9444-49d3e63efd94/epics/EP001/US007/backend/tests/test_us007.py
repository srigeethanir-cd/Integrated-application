# tests/test_delete_task.py

from fastapi.testclient import TestClient
from main import app
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base, Task

# Create a test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create a test client
client = TestClient(app)

# Override the database dependency
app.dependency_overrides["get_db"] = override_get_db

def test_delete_task():
    # Create a task
    task = {"title": "Test Task", "description": "This is a test task"}
    response = client.post("/tasks/", json=task)
    assert response.status_code == 201
    task_id = response.json()["id"]

    # Delete the task
    response = client.delete(f"/tasks/{task_id}")
    assert response.status_code == 200

    # Check if the task is deleted
    response = client.get(f"/tasks/{task_id}")
    assert response.status_code == 404

def test_delete_non_existent_task():
    # Delete a non-existent task
    response = client.delete("/tasks/999")
    assert response.status_code == 404