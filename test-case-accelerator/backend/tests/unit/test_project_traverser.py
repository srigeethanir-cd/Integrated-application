import pytest
from pathlib import Path
from app.services.dependency.project_traverser import ProjectTraverser


def test_project_traverser_scans_source_files_and_ignores_dependencies(tmp_path: Path) -> None:
    # Set up directories
    app_dir = tmp_path / "app"
    app_dir.mkdir()
    venv_dir = tmp_path / ".venv"
    venv_dir.mkdir()
    node_dir = tmp_path / "node_modules"
    node_dir.mkdir()
    
    # Create valid files
    main_py = app_dir / "main.py"
    main_py.write_text("print('Hello')", encoding="utf-8")
    
    # Create files to ignore
    pytest_py = venv_dir / "Lib" / "site-packages" / "_pytest" / "config" / "__init__.py"
    pytest_py.parent.mkdir(parents=True)
    pytest_py.write_text("pass", encoding="utf-8")
    
    package_json = node_dir / "index.js"
    package_json.write_text("console.log('js')", encoding="utf-8")
    
    # Scan with ProjectTraverser
    traverser = ProjectTraverser()
    scanned_files = list(traverser.scan(tmp_path))
    
    # Assert main.py is found, but ignored files are not
    assert main_py in scanned_files
    assert pytest_py not in scanned_files
    assert package_json not in scanned_files
