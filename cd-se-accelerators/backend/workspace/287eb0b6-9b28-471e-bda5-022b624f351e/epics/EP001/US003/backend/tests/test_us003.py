# tests/test_dashboard.py
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_view_dashboard():
    # Arrange
    # Create a test user and tasks
    user_id = 1
    tasks = [
        {"id": 1, "title": "Task 1", "user_id": user_id},
        {"id": 2, "title": "Task 2", "user_id": user_id},
    ]

    # Act
    response = client.get(f"/dashboard/{user_id}")

    # Assert
    assert response.status_code == 200
    assert "tasks" in response.json()
    assert len(response.json()["tasks"]) == len(tasks)
    assert "task_count" in response.json()
    assert response.json()["task_count"] == len(tasks)

def test_view_dashboard_empty():
    # Arrange
    # Create a test user with no tasks
    user_id = 2

    # Act
    response = client.get(f"/dashboard/{user_id}")

    # Assert
    assert response.status_code == 200
    assert "tasks" in response.json()
    assert len(response.json()["tasks"]) == 0
    assert "task_count" in response.json()
    assert response.json()["task_count"] == 0