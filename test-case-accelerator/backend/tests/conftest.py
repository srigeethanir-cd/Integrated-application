import uuid
from collections.abc import Callable, Iterator
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.database.models.project import Project, ProjectSourceType, ProjectStatus
from app.main import app

@pytest.fixture
def mocker():
    """Simple mocker fixture using unittest.mock.patch"""
    from unittest.mock import patch
    class SimpleMocker:
        def __init__(self):
            self._patch = patch
        def patch(self, target, **kwargs):
            """Patch the target and return the started mock.
            Mirrors pytest-mock's behavior where `mocker.patch` returns a MagicMock.
            """
            return self._patch(target, **kwargs).start()
    return SimpleMocker()

@pytest.fixture
def project_factory() -> Callable[..., Project]:
    def create_project(**overrides: object) -> Project:
        values: dict[str, object] = {
            "id": uuid.UUID("12345678-1234-5678-1234-567812345678"),
            "name": "Example project",
            "description": "Project description",
            "source_type": ProjectSourceType.ZIP,
            "github_url": None,
            "storage_path": "/storage/projects/example",
            "status": ProjectStatus.UPLOADED,
            "created_at": datetime(2026, 1, 1, tzinfo=UTC),
            "updated_at": datetime(2026, 1, 1, tzinfo=UTC),
        }
        values.update(overrides)
        return Project(**values)

    return create_project


@pytest.fixture
def client() -> Iterator[TestClient]:
    # Integration tests replace persistence dependencies with controlled
    # fakes; schema-drift behavior is covered independently.
    with (
        patch("app.main.validate_database_schema"),
        patch("app.main.check_redis_health"),
        patch("app.main.close_redis_client"),
        TestClient(app) as test_client,
    ):
        yield test_client
    app.dependency_overrides.clear()
