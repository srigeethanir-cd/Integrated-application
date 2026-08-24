import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_edit_task():
    # Create a new task
    task_data = {"title": "New Task", "status": "pending"}
    response = client.post("/tasks/", json=task_data)
    assert response.status_code == 201
    task_id = response.json()["id"]

    # Edit the task
    updated_task_data = {"title": "Updated Task", "status": "in_progress"}
    response = client.put(f"/tasks/{task_id}", json=updated_task_data)
    assert response.status_code == 200
    updated_task = response.json()

    # Check if the task title and status are updated
    assert updated_task["title"] == updated_task_data["title"]
    assert updated_task["status"] == updated_task_data["status"]

def test_edit_task_invalid_id():
    # Edit a task with an invalid id
    updated_task_data = {"title": "Updated Task", "status": "in_progress"}
    response = client.put("/tasks/999", json=updated_task_data)
    assert response.status_code == 404

def test_edit_task_invalid_data():
    # Create a new task
    task_data = {"title": "New Task", "status": "pending"}
    response = client.post("/tasks/", json=task_data)
    assert response.status_code == 201
    task_id = response.json()["id"]

    # Edit the task with invalid data
    updated_task_data = {"title": "", "status": "invalid_status"}
    response = client.put(f"/tasks/{task_id}", json=updated_task_data)
    assert response.status_code == 422