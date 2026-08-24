# tests/test_edit_task.py
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

    # Verify the task has been updated
    assert updated_task["title"] == updated_task_data["title"]
    assert updated_task["status"] == updated_task_data["status"]

def test_edit_task_title():
    # Create a new task
    task_data = {"title": "New Task", "status": "pending"}
    response = client.post("/tasks/", json=task_data)
    assert response.status_code == 201
    task_id = response.json()["id"]

    # Edit the task title
    updated_task_data = {"title": "Updated Task Title"}
    response = client.patch(f"/tasks/{task_id}", json=updated_task_data)
    assert response.status_code == 200
    updated_task = response.json()

    # Verify the task title has been updated
    assert updated_task["title"] == updated_task_data["title"]

def test_edit_task_status():
    # Create a new task
    task_data = {"title": "New Task", "status": "pending"}
    response = client.post("/tasks/", json=task_data)
    assert response.status_code == 201
    task_id = response.json()["id"]

    # Edit the task status
    updated_task_data = {"status": "in_progress"}
    response = client.patch(f"/tasks/{task_id}", json=updated_task_data)
    assert response.status_code == 200
    updated_task = response.json()

    # Verify the task status has been updated
    assert updated_task["status"] == updated_task_data["status"]