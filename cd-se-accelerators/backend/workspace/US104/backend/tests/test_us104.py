# tests/test_component.py

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_broken_feature():
    """
    Test case for US104: Broken Feature
    Description: Invalid Python Syntax
    """
    # Arrange
    # No specific arrangement needed for this test case

    # Act
    response = client.get("/component")

    # Assert
    assert response.status_code == 500, "Expected 500 Internal Server Error"
    assert response.json()["detail"] == "Invalid Python syntax", "Expected error message"