# tests/test_filter_tasks.py

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_filter_tasks_by_status():
    # Create test tasks
    task1 = {"title": "Task 1", "status": "completed"}
    task2 = {"title": "Task 2", "status": "pending"}
    task3 = {"title": "Task 3", "status": "completed"}

    # Send POST requests to create tasks
    client.post("/tasks/", json=task1)
    client.post("/tasks/", json=task2)
    client.post("/tasks/", json=task3)

    # Filter tasks by status
    response_completed = client.get("/tasks/", params={"status": "completed"})
    response_pending = client.get("/tasks/", params={"status": "pending"})

    # Assert response status code
    assert response_completed.status_code == 200
    assert response_pending.status_code == 200

    # Assert response content
    assert len(response_completed.json()) == 2
    assert len(response_pending.json()) == 1

    # Assert task status
    for task in response_completed.json():
        assert task["status"] == "completed"
    for task in response_pending.json():
        assert task["status"] == "pending"

def test_filter_tasks_by_invalid_status():
    # Filter tasks by invalid status
    response = client.get("/tasks/", params={"status": "invalid"})

    # Assert response status code
    assert response.status_code == 200

    # Assert response content
    assert len(response.json()) == 0