# tests/test_component.py
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_create_task():
    # Arrange
    task_title = "New Task"

    # Act
    response = client.post(
        "/tasks/",
        json={"title": task_title},
    )

    # Assert
    assert response.status_code == 201
    assert response.json()["title"] == task_title

def test_create_task_with_empty_title():
    # Arrange
    task_title = ""

    # Act
    response = client.post(
        "/tasks/",
        json={"title": task_title},
    )

    # Assert
    assert response.status_code == 422

def test_create_task_with_long_title():
    # Arrange
    task_title = "a" * 1001

    # Act
    response = client.post(
        "/tasks/",
        json={"title": task_title},
    )

    # Assert
    assert response.status_code == 422