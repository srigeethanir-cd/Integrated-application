import io
import uuid
import zipfile
from unittest.mock import Mock

from app.dependencies.code_understanding import get_code_understanding_service
from app.dependencies.export import get_pytest_export_service
from app.dependencies.project import get_project_repository
from app.main import app
from app.services.export.pytest_export_service import PytestExportService


def _generation(path: str = "tests/services/test_user.py") -> dict:
    return {
        "test_generation": {
            "generated_test_cases": [
                {
                    "id": "UT-1",
                    "title": "loads user",
                    "category": "positive",
                    "traceability": {"suggested_test_path": path},
                    "unit_test": {
                        "generated_code": "def test_load_user():\n    assert 2 + 2 == 4\n"
                    },
                }
            ]
        }
    }


def test_export_endpoint_streams_zip_and_uses_project_name(client) -> None:
    project_id = uuid.uuid4()
    repository = Mock()
    project = Mock()
    project.name = "Export Project"
    repository.get_by_id.return_value = project
    understanding = Mock()
    understanding.get_latest_pipeline_state.return_value = _generation()
    app.dependency_overrides[get_project_repository] = lambda: repository
    app.dependency_overrides[get_code_understanding_service] = lambda: understanding
    app.dependency_overrides[get_pytest_export_service] = lambda: PytestExportService(
        generator_version="test"
    )

    response = client.get(f"/projects/{project_id}/exports/test-suite")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"
    assert 'filename="test-suite.zip"' in response.headers["content-disposition"]
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        assert "test-suite/tests/services/test_user.py" in archive.namelist()
        assert "# Export Project" in archive.read("test-suite/README.md").decode()


def test_export_endpoint_returns_structured_not_ready_error(client) -> None:
    project_id = uuid.uuid4()
    repository = Mock()
    project = Mock()
    project.name = "Empty"
    repository.get_by_id.return_value = project
    understanding = Mock()
    understanding.get_latest_pipeline_state.return_value = {
        "test_generation": {"generated_test_cases": []}
    }
    app.dependency_overrides[get_project_repository] = lambda: repository
    app.dependency_overrides[get_code_understanding_service] = lambda: understanding

    response = client.get(f"/projects/{project_id}/exports/test-suite")

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "export_not_ready"


def test_export_endpoint_rejects_corrupted_artifact(client) -> None:
    project_id = uuid.uuid4()
    repository = Mock()
    project = Mock()
    project.name = "Unsafe"
    repository.get_by_id.return_value = project
    understanding = Mock()
    understanding.get_latest_pipeline_state.return_value = _generation(
        "../../test_escape.py"
    )
    app.dependency_overrides[get_project_repository] = lambda: repository
    app.dependency_overrides[get_code_understanding_service] = lambda: understanding

    response = client.get(f"/projects/{project_id}/exports/test-suite")

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "corrupted_export_artifact"
