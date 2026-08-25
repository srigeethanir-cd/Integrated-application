import io
import os
from pathlib import Path
import sqlite3
import subprocess
from urllib.error import HTTPError
from urllib.request import urlopen
from unittest.mock import Mock

import pytest

from app.services.runtime.sut_backend_manager import (
    SUTBackendManager,
    SUTBackendStartupError,
)
from app.services.runtime.openapi_metadata_service import OpenAPIMetadataService


EXPECTED = [{"route": "/items", "method": "GET"}]
MATCHING_OPENAPI = {
    "openapi": "3.1.0",
    "paths": {"/items": {"get": {"responses": {"200": {}}}}},
}


class FakeProcess:
    def __init__(self, *, exit_code=None, output="startup output\n"):
        self._exit_code = exit_code
        self.stdout = io.StringIO(output)
        self.terminated = False
        self.killed = False

    def poll(self):
        return self._exit_code

    def terminate(self):
        self.terminated = True
        self._exit_code = 0

    def kill(self):
        self.killed = True
        self._exit_code = -9

    def wait(self, timeout=None):
        return self._exit_code


def _source(tmp_path: Path, content: str | None = None) -> Path:
    source = tmp_path / "source"
    source.mkdir()
    (source / "main.py").write_text(
        content
        or "from fastapi import FastAPI\napp = FastAPI()\n",
        encoding="utf-8",
    )
    return source


def test_uploaded_backend_is_started_waited_for_and_stopped(tmp_path) -> None:
    openapi = Mock()
    openapi.load_document.side_effect = [
        (None, "refused"),
        (None, "starting"),
        (MATCHING_OPENAPI, None),
    ]
    process = FakeProcess()
    factory = Mock(return_value=process)
    manager = SUTBackendManager(
        openapi,
        process_factory=factory,
        sleep=lambda _: None,
        port_probe=lambda: False,
    )

    with manager.ensure_running(
        _source(tmp_path), expected_endpoints=EXPECTED
    ) as lease:
        assert lease.spawned is True
        assert lease.document == MATCHING_OPENAPI
        command = factory.call_args.args[0]
        assert command[-5:] == [
            "main:app", "--host", "127.0.0.1", "--port", "8001"
        ]

    assert process.terminated is True
    assert process.killed is False


def test_spawned_uvicorn_emits_and_captures_unhandled_asgi_traceback(
    tmp_path,
) -> None:
    if SUTBackendManager._port_8001_in_use():
        pytest.skip("Port 8001 is already in use")
    source = _source(
        tmp_path,
        "from fastapi import FastAPI\n"
        "app = FastAPI()\n"
        "@app.get('/explode')\n"
        "def explode():\n"
        "    raise RuntimeError('observable SUT failure')\n",
    )
    manager = SUTBackendManager(OpenAPIMetadataService())

    with manager.ensure_running(
        source,
        expected_endpoints=[{"route": "/explode", "method": "GET"}],
    ) as lease:
        with pytest.raises(HTTPError) as response:
            urlopen("http://127.0.0.1:8001/explode", timeout=5)
        assert response.value.code == 500
        captured = "\n".join(
            lease.captured_output(wait_for_diagnostics=True)
        )

    assert "ERROR:    Exception in ASGI application" in captured
    assert "Traceback (most recent call last):" in captured
    assert "RuntimeError: observable SUT failure" in captured


def test_existing_uploaded_backend_is_reused(tmp_path) -> None:
    openapi = Mock()
    openapi.load_document.return_value = (MATCHING_OPENAPI, None)
    factory = Mock()
    manager = SUTBackendManager(openapi, process_factory=factory)

    lease = manager.ensure_running(
        _source(tmp_path), expected_endpoints=EXPECTED
    )

    assert lease.spawned is False
    factory.assert_not_called()
    lease.close()


def test_startup_failure_contains_entry_command_output_and_reason(
    tmp_path,
) -> None:
    openapi = Mock()
    openapi.load_document.return_value = (None, "refused")
    process = FakeProcess(exit_code=1, output="ImportError: missing package\n")
    manager = SUTBackendManager(
        openapi,
        process_factory=Mock(return_value=process),
        port_probe=lambda: False,
    )

    with pytest.raises(SUTBackendStartupError) as captured:
        manager.ensure_running(
            _source(tmp_path), expected_endpoints=EXPECTED
        )

    message = str(captured.value)
    assert "Detected entry point: main:app" in message
    assert "Startup command:" in message
    assert "uvicorn exited with code 1" in message
    assert "ImportError: missing package" in message


def test_startup_timeout_terminates_spawned_process(tmp_path) -> None:
    now = [0.0]

    def sleep(delay):
        now[0] += delay

    openapi = Mock()
    openapi.load_document.return_value = (None, "refused")
    process = FakeProcess()
    manager = SUTBackendManager(
        openapi,
        process_factory=Mock(return_value=process),
        clock=lambda: now[0],
        sleep=sleep,
        port_probe=lambda: False,
    )

    with pytest.raises(SUTBackendStartupError, match="timed out"):
        manager.ensure_running(
            _source(tmp_path),
            expected_endpoints=EXPECTED,
            timeout_seconds=1,
        )

    assert process.terminated is True


def test_incorrect_process_on_port_8001_is_not_modified(tmp_path) -> None:
    openapi = Mock()
    openapi.load_document.return_value = (
        {"openapi": "3.1.0", "paths": {"/accelerator": {"get": {}}}},
        None,
    )
    factory = Mock()
    manager = SUTBackendManager(openapi, process_factory=factory)

    with pytest.raises(
        SUTBackendStartupError,
        match="different application",
    ):
        manager.ensure_running(
            _source(tmp_path), expected_endpoints=EXPECTED
        )

    factory.assert_not_called()


def test_starlette_entry_point_is_detected(tmp_path) -> None:
    entry = SUTBackendManager.detect_entry_point(_source(
        tmp_path,
        "from starlette.applications import Starlette\n"
        "app = Starlette()\n",
    ))

    assert entry.framework == "Starlette"
    assert entry.import_target == "main:app"


def test_nested_fastapi_entry_point_is_discovered_recursively(tmp_path) -> None:
    source = tmp_path / "source"
    backend = source / "backend"
    backend.mkdir(parents=True)
    (backend / "service.py").write_text(
        "from fastapi import FastAPI\napp = FastAPI()\n",
        encoding="utf-8",
    )

    entry = SUTBackendManager.detect_entry_point(source)

    assert entry.framework == "FastAPI"
    assert entry.import_target == "backend.service:app"


def test_nested_application_root_supports_top_level_app_imports(tmp_path) -> None:
    source = tmp_path / "source"
    project = source / "project"
    routers = project / "app" / "routers"
    routers.mkdir(parents=True)
    (project / "app" / "__init__.py").write_text("", encoding="utf-8")
    (routers / "__init__.py").write_text("", encoding="utf-8")
    (routers / "items.py").write_text("router = object()\n", encoding="utf-8")
    (project / "main.py").write_text(
        "from fastapi import FastAPI\n"
        "from app.routers import items\n"
        "app = FastAPI()\n",
        encoding="utf-8",
    )
    openapi = Mock()
    openapi.load_document.side_effect = [
        (None, "refused"), (MATCHING_OPENAPI, None),
    ]

    def process_factory(command, **options):
        imported = subprocess.run(
            [
                command[0], "-c",
                "from app.routers import items; "
                "from importlib import import_module; "
                "import_module('project.main')",
            ],
            cwd=options["cwd"],
            env=options["env"],
            capture_output=True,
            text=True,
            check=False,
        )
        assert imported.returncode == 0, imported.stderr
        return FakeProcess()

    manager = SUTBackendManager(
        openapi,
        process_factory=process_factory,
        sleep=lambda _: None,
        port_probe=lambda: False,
    )

    with manager.ensure_running(source, expected_endpoints=EXPECTED) as lease:
        runtime = lease.runtime_environment
        assert runtime is not None
        application_root = runtime.source_directory / "project"
        assert lease.entry_point is not None
        assert lease.entry_point.import_target == "project.main:app"
        configured_root = Path(
            runtime.environment["PYTHONPATH"].split(os.pathsep)[0]
        )
        assert configured_root.samefile(application_root)


def test_main_module_outranks_other_nested_applications(tmp_path) -> None:
    source = tmp_path / "source"
    backend = source / "backend"
    backend.mkdir(parents=True)
    (backend / "service.py").write_text(
        "from fastapi import FastAPI\nservice_app = FastAPI()\n",
        encoding="utf-8",
    )
    (backend / "main.py").write_text(
        "from fastapi import FastAPI\napp = FastAPI()\n",
        encoding="utf-8",
    )

    entry = SUTBackendManager.detect_entry_point(source)

    assert entry.import_target == "backend.main:app"


def test_router_aggregation_and_test_reference_rank_candidates(tmp_path) -> None:
    source = tmp_path / "source"
    backend = source / "backend"
    tests = source / "tests"
    backend.mkdir(parents=True)
    tests.mkdir()
    (backend / "plain.py").write_text(
        "from fastapi import FastAPI\napp = FastAPI()\n",
        encoding="utf-8",
    )
    (backend / "api.py").write_text(
        "from fastapi import FastAPI\n"
        "from backend.items_router import router\n"
        "app = FastAPI()\n"
        "app.include_router(router)\n",
        encoding="utf-8",
    )
    (tests / "test_api.py").write_text(
        "from backend.api import app\n",
        encoding="utf-8",
    )

    entry = SUTBackendManager.detect_entry_point(source)

    assert entry.import_target == "backend.api:app"


def test_all_application_assignments_are_ranked(caplog, tmp_path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "applications.py").write_text(
        "from fastapi import FastAPI\n"
        "first = FastAPI()\n"
        "second = FastAPI()\n",
        encoding="utf-8",
    )

    SUTBackendManager.detect_entry_point(source)

    ranking_logs = [
        record.message for record in caplog.records
        if "SUT ASGI candidate ranking" in record.message
    ]
    assert len(ranking_logs) == 2
    assert any("applications:first" in message for message in ranking_logs)
    assert any("applications:second" in message for message in ranking_logs)


def test_alembic_project_is_upgraded_before_uvicorn(tmp_path) -> None:
    source = _source(tmp_path)
    (source / "alembic.ini").write_text(
        "[alembic]\nscript_location = alembic\n",
        encoding="utf-8",
    )
    (source / "alembic").mkdir()
    events = []
    runner = Mock(side_effect=lambda *args, **kwargs: (
        events.append("initialize")
        or subprocess.CompletedProcess(args[0], 0, "", "")
    ))
    process = FakeProcess()
    factory = Mock(side_effect=lambda *args, **kwargs: (
        events.append("uvicorn") or process
    ))
    openapi = Mock()
    openapi.load_document.side_effect = [
        (None, "refused"), (MATCHING_OPENAPI, None),
    ]
    manager = SUTBackendManager(
        openapi,
        process_factory=factory,
        command_runner=runner,
        sleep=lambda _: None,
        port_probe=lambda: False,
    )

    with manager.ensure_running(source, expected_endpoints=EXPECTED):
        initialization = runner.call_args.args[0]
        environment = runner.call_args.kwargs["env"]
        assert "command.upgrade(cfg, 'head')" in initialization[-1]
        assert environment["DATABASE_URL"].startswith("sqlite:///")
        assert environment["RUNTIME_VALIDATION"] == "true"

    assert events == ["initialize", "uvicorn"]


def test_sqlalchemy_project_creates_isolated_database_and_cleans_up(
    tmp_path,
) -> None:
    source = _source(
        tmp_path,
        "from fastapi import FastAPI\n"
        "from models import Item\n"
        "app = FastAPI()\n",
    )
    (source / "database.py").write_text(
        "import os\n"
        "from sqlalchemy import create_engine\n"
        "from sqlalchemy.orm import declarative_base\n"
        "engine = create_engine(os.environ['DATABASE_URL'])\n"
        "Base = declarative_base()\n",
        encoding="utf-8",
    )
    (source / "models.py").write_text(
        "from sqlalchemy import Column, Integer\n"
        "from database import Base\n"
        "class Item(Base):\n"
        "    __tablename__ = 'items'\n"
        "    id = Column(Integer, primary_key=True)\n",
        encoding="utf-8",
    )
    openapi = Mock()
    openapi.load_document.side_effect = [
        (None, "refused"), (MATCHING_OPENAPI, None),
    ]
    factory = Mock(return_value=FakeProcess())
    manager = SUTBackendManager(
        openapi,
        process_factory=factory,
        sleep=lambda _: None,
        port_probe=lambda: False,
    )

    lease = manager.ensure_running(source, expected_endpoints=EXPECTED)
    runtime = lease.runtime_environment
    assert runtime is not None
    runtime_root = runtime.source_directory.parent
    database_path = Path(runtime.database_url.removeprefix("sqlite:///"))
    assert database_path.is_file()
    connection = sqlite3.connect(database_path)
    try:
        tables = {
            row[0] for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
    finally:
        connection.close()
    assert "items" in tables
    assert not (source / "runtime.db").exists()

    lease.close()

    assert not runtime_root.exists()


def test_sqlalchemy_initialization_imports_separate_model_module(
    tmp_path, caplog,
) -> None:
    source = _source(
        tmp_path,
        "from fastapi import FastAPI\n"
        "app = FastAPI()\n",
    )
    (source / "database.py").write_text(
        "import os\n"
        "from sqlalchemy import create_engine\n"
        "from sqlalchemy.orm import declarative_base\n"
        "engine = create_engine(os.environ['DATABASE_URL'])\n"
        "Base = declarative_base()\n",
        encoding="utf-8",
    )
    (source / "models.py").write_text(
        "from sqlalchemy import Column, Integer\n"
        "from database import Base\n"
        "class Item(Base):\n"
        "    __tablename__ = 'items'\n"
        "    id = Column(Integer, primary_key=True)\n",
        encoding="utf-8",
    )
    openapi = Mock()
    openapi.load_document.side_effect = [
        (None, "refused"), (MATCHING_OPENAPI, None),
    ]
    manager = SUTBackendManager(
        openapi,
        process_factory=Mock(return_value=FakeProcess()),
        sleep=lambda _: None,
        port_probe=lambda: False,
    )

    with caplog.at_level("INFO"):
        lease = manager.ensure_running(source, expected_endpoints=EXPECTED)
    runtime = lease.runtime_environment
    assert runtime is not None
    database_path = Path(runtime.database_url.removeprefix("sqlite:///"))
    connection = sqlite3.connect(database_path)
    try:
        tables = {
            row[0] for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
    finally:
        connection.close()

    assert tables == {"items"}
    assert "metadata_tables=['items']" in caplog.text
    assert "tables_created=1" in caplog.text
    assert "database paths initialization=" in caplog.text
    assert "runtime_application=" in caplog.text
    assert "runtime.db" in caplog.text
    lease.close()


def test_relative_sqlite_url_uses_same_directory_as_runtime_application(
    tmp_path,
) -> None:
    source = tmp_path / "source"
    package = source / "app"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("", encoding="utf-8")
    (package / "main.py").write_text(
        "from fastapi import FastAPI\n"
        "app = FastAPI()\n",
        encoding="utf-8",
    )
    (package / "database.py").write_text(
        "from sqlalchemy import create_engine\n"
        "from sqlalchemy.orm import declarative_base\n"
        "engine = create_engine('sqlite:///./test.db')\n"
        "Base = declarative_base()\n",
        encoding="utf-8",
    )
    (package / "models.py").write_text(
        "from sqlalchemy import Column, Integer\n"
        "from app.database import Base\n"
        "class Item(Base):\n"
        "    __tablename__ = 'items'\n"
        "    id = Column(Integer, primary_key=True)\n",
        encoding="utf-8",
    )
    openapi = Mock()
    openapi.load_document.side_effect = [
        (None, "refused"), (MATCHING_OPENAPI, None),
    ]
    manager = SUTBackendManager(
        openapi,
        process_factory=Mock(return_value=FakeProcess()),
        sleep=lambda _: None,
        port_probe=lambda: False,
    )

    lease = manager.ensure_running(source, expected_endpoints=EXPECTED)
    runtime = lease.runtime_environment
    assert runtime is not None
    runtime_package = runtime.source_directory / "app"

    assert (runtime_package / "test.db").is_file()
    assert not (runtime.source_directory / "test.db").exists()
    connection = sqlite3.connect(runtime_package / "test.db")
    try:
        assert connection.execute(
            "SELECT name FROM sqlite_master WHERE name='items'"
        ).fetchone() == ("items",)
    finally:
        connection.close()
    lease.close()


def test_project_without_database_skips_initialization(tmp_path) -> None:
    openapi = Mock()
    openapi.load_document.side_effect = [
        (None, "refused"), (MATCHING_OPENAPI, None),
    ]
    runner = Mock()
    manager = SUTBackendManager(
        openapi,
        process_factory=Mock(return_value=FakeProcess()),
        command_runner=runner,
        sleep=lambda _: None,
        port_probe=lambda: False,
    )

    with manager.ensure_running(
        _source(tmp_path), expected_endpoints=EXPECTED
    ) as lease:
        assert lease.runtime_environment is not None
        assert lease.runtime_environment.strategy == "none"

    runner.assert_not_called()


def test_multiple_runtime_executions_use_distinct_databases(tmp_path) -> None:
    source = _source(tmp_path)
    (source / "database.py").write_text(
        "from sqlalchemy.orm import declarative_base\n"
        "Base = declarative_base()\n",
        encoding="utf-8",
    )
    runner = Mock(return_value=subprocess.CompletedProcess([], 0, "", ""))
    database_urls = []
    runtime_roots = []

    for _ in range(2):
        openapi = Mock()
        openapi.load_document.side_effect = [
            (None, "refused"), (MATCHING_OPENAPI, None),
        ]
        manager = SUTBackendManager(
            openapi,
            process_factory=Mock(return_value=FakeProcess()),
            command_runner=runner,
            sleep=lambda _: None,
            port_probe=lambda: False,
        )
        lease = manager.ensure_running(source, expected_endpoints=EXPECTED)
        runtime = lease.runtime_environment
        assert runtime is not None
        database_urls.append(runtime.database_url)
        runtime_roots.append(runtime.source_directory.parent)
        lease.close()

    assert database_urls[0] != database_urls[1]
    assert all(not path.exists() for path in runtime_roots)
