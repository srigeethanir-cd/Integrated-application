# tests/test_component.py
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_mark_task_complete():
    # Arrange
    task_id = 1
    task_status = "in_progress"

    # Create a task
    response = client.post(
        "/tasks/",
        json={"title": "Test Task", "description": "Test Task Description"},
    )
    assert response.status_code == 201
    task_id = response.json()["id"]

    # Act
    response = client.patch(
        f"/tasks/{task_id}/complete",
    )

    # Assert
    assert response.status_code == 200
    assert response.json()["status"] == "completed"

def test_mark_task_complete_invalid_task_id():
    # Act
    response = client.patch(
        "/tasks/999/complete",
    )

    # Assert
    assert response.status_code == 404

def test_mark_task_complete_already_completed():
    # Arrange
    task_id = 1
    task_status = "in_progress"

    # Create a task
    response = client.post(
        "/tasks/",
        json={"title": "Test Task", "description": "Test Task Description"},
    )
    assert response.status_code == 201
    task_id = response.json()["id"]

    # Mark task as completed
    response = client.patch(
        f"/tasks/{task_id}/complete",
    )
    assert response.status_code == 200

    # Act
    response = client.patch(
        f"/tasks/{task_id}/complete",
    )

    # Assert
    assert response.status_code == 400