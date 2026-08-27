"""
Tests for ZIP Upload and Input Preprocessing support in Framework Detection API.
"""

import io
import os
import shutil
import tempfile
import zipfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.utils.input_preprocessor import get_project_workspace
from app.utils.project_locator import locate_project_root
from app.utils.temp_workspace import _DEFAULT_TEMP_ROOT, TempWorkspace
from app.utils.zip_handler import ZipHandler

client = TestClient(app)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test fixtures and clean up afterwards."""
    td = tempfile.mkdtemp()
    yield Path(td)
    shutil.rmtree(td, ignore_errors=True)


def create_zip(target_zip_path: Path, files: dict[str, str]) -> Path:
    """Helper to create a zip file with a dict of relative paths -> text content."""
    with zipfile.ZipFile(target_zip_path, "w") as zf:
        for rel_path, content in files.items():
            zf.writestr(rel_path, content)
    return target_zip_path


# -----------------------------------------------------------------------------
# Unit Tests for ZipHandler & Security
# -----------------------------------------------------------------------------


def test_zip_handler_extract_valid(temp_dir):
    zip_path = temp_dir / "valid.zip"
    create_zip(
        zip_path,
        {
            "package.json": '{"dependencies": {"react": "^18.0.0"}}',
            "src/App.js": "export default function App() { return <h1>Hello</h1>; }",
        },
    )

    dest_dir = temp_dir / "extracted"
    handler = ZipHandler()
    elapsed_ms = handler.extract(zip_path, dest_dir)

    assert elapsed_ms >= 0
    assert (dest_dir / "package.json").exists()
    assert (dest_dir / "src" / "App.js").exists()


def test_zip_handler_corrupted_file(temp_dir):
    corrupt_zip = temp_dir / "corrupt.zip"
    corrupt_zip.write_bytes(b"THIS IS NOT A ZIP ARCHIVE")

    handler = ZipHandler()
    with pytest.raises(ValueError, match="ZIP archive is corrupted"):
        handler.extract(corrupt_zip, temp_dir / "extracted")


def test_zip_handler_traversal_attack(temp_dir):
    bad_zip = temp_dir / "malicious.zip"
    with zipfile.ZipFile(bad_zip, "w") as zf:
        zf.writestr("../../evil.txt", "hacked")

    handler = ZipHandler()
    with pytest.raises(ValueError, match="Unsafe ZIP entry detected"):
        handler.extract(bad_zip, temp_dir / "extracted")


# -----------------------------------------------------------------------------
# Unit Tests for Project Locator
# -----------------------------------------------------------------------------


def test_project_locator_root_level(temp_dir):
    (temp_dir / "package.json").write_text('{"dependencies": {"react": "18"}}')
    (temp_dir / "src").mkdir()

    root = locate_project_root(temp_dir)
    assert root.resolve() == temp_dir.resolve()


def test_project_locator_nested_wrapper(temp_dir):
    nested = temp_dir / "my-react-app"
    nested.mkdir()
    (nested / "package.json").write_text('{"dependencies": {"react": "18"}}')
    (nested / "src").mkdir()

    root = locate_project_root(temp_dir)
    assert root.resolve() == nested.resolve()


def test_project_locator_empty_directory(temp_dir):
    empty_dir = temp_dir / "empty"
    empty_dir.mkdir()

    with pytest.raises(ValueError, match="Project directory is empty"):
        locate_project_root(empty_dir)


def test_project_locator_no_indicators(temp_dir):
    no_indicators = temp_dir / "no_indicators"
    no_indicators.mkdir()
    (no_indicators / "file1.txt").write_text("hello")
    (no_indicators / "file2.txt").write_text("world")

    with pytest.raises(ValueError, match="No frontend project detected inside ZIP"):
        locate_project_root(no_indicators)


# -----------------------------------------------------------------------------
# API Tests for POST /framework/detect
# -----------------------------------------------------------------------------


def test_api_detect_directory_success(temp_dir):
    proj_dir = temp_dir / "my-react-app"
    proj_dir.mkdir()
    (proj_dir / "package.json").write_text('{"dependencies": {"react": "^18.2.0"}}')
    (proj_dir / "src").mkdir()
    (proj_dir / "src" / "App.jsx").write_text("export default function App() {}")

    response = client.post("/framework/detect", json={"project_path": str(proj_dir)})
    assert response.status_code == 200
    data = response.json()
    assert data["framework"] == "React"
    assert data["confidence"] > 0


def test_api_detect_zip_root_success(temp_dir):
    zip_path = temp_dir / "react-project.zip"
    create_zip(
        zip_path,
        {
            "package.json": '{"dependencies": {"react": "^18.2.0"}}',
            "src/App.jsx": "export default function App() {}",
        },
    )

    response = client.post("/framework/detect", json={"project_path": str(zip_path)})
    assert response.status_code == 200
    data = response.json()
    assert data["framework"] == "React"
    assert data["confidence"] > 0


def test_api_detect_zip_nested_wrapper_success(temp_dir):
    zip_path = temp_dir / "nested-nextjs.zip"
    create_zip(
        zip_path,
        {
            "my-next-app/package.json": '{"dependencies": {"next": "13.0.0", "react": "18.0.0"}}',
            "my-next-app/next.config.js": "module.exports = {};",
            "my-next-app/src/pages/index.js": "export default function Home() {}",
        },
    )

    response = client.post("/framework/detect", json={"project_path": str(zip_path)})
    assert response.status_code == 200
    data = response.json()
    assert data["framework"] == "Next.js"


def test_api_detect_path_not_found():
    non_existent = str(Path(tempfile.gettempdir()) / "non_existent_folder_12345")
    response = client.post("/framework/detect", json={"project_path": non_existent})
    assert response.status_code == 404
    assert "does not exist" in response.json()["detail"]


def test_api_detect_unsupported_file_extension(temp_dir):
    unsupported_file = temp_dir / "project.tar.gz"
    unsupported_file.write_bytes(b"dummy archive content")

    response = client.post(
        "/framework/detect", json={"project_path": str(unsupported_file)}
    )
    assert response.status_code == 400
    assert "Unsupported file format" in response.json()["detail"]


def test_api_detect_corrupted_zip(temp_dir):
    corrupt_zip = temp_dir / "broken.zip"
    corrupt_zip.write_bytes(b"INVALID_ZIP_HEADER_DATA")

    response = client.post(
        "/framework/detect", json={"project_path": str(corrupt_zip)}
    )
    assert response.status_code == 400
    assert "corrupted" in response.json()["detail"].lower()


def test_api_detect_zip_cleanup(temp_dir):
    zip_path = temp_dir / "clean_test.zip"
    create_zip(
        zip_path,
        {
            "package.json": '{"dependencies": {"react": "^18.2.0"}}',
        },
    )

    # Check temp dir count before
    _DEFAULT_TEMP_ROOT.mkdir(parents=True, exist_ok=True)
    before_dirs = set(_DEFAULT_TEMP_ROOT.glob("*"))

    response = client.post("/framework/detect", json={"project_path": str(zip_path)})
    assert response.status_code == 200

    # Check temp dir count after - no leftover workspace dirs
    after_dirs = set(_DEFAULT_TEMP_ROOT.glob("*"))
    assert after_dirs == before_dirs
