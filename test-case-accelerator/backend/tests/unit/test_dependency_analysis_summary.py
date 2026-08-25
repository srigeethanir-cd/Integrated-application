from types import SimpleNamespace

from app.services.dependency.analysis_summary import build_dependency_analysis


def test_analysis_detects_framework_runtime_and_filters_local_modules() -> None:
    files = [
        SimpleNamespace(
            path="project/source/main.py",
            language="python",
            is_entry_point=True,
            imports=[
                "fastapi", "sqlalchemy", "uvicorn", "passlib", "jose",
                "email_validator", "pytest", "axios", "app.routers",
                "main", "backend.internal", "datetime", "json", "typing", "re",
            ],
        ),
        SimpleNamespace(
            path="project/source/app/routers/items.py",
            language="python",
            is_entry_point=False,
            imports=["pydantic", "app.services.items"],
        ),
    ]

    result = build_dependency_analysis(files)

    assert result["backend_framework"] == "FastAPI Backend"
    assert result["runtime"] == "Python"
    assert result["dependencies"] == [
        "axios", "email_validator", "fastapi", "jose", "passlib",
        "pydantic", "pytest", "sqlalchemy", "uvicorn",
    ]
    assert "main" not in result["dependencies"]
    assert "app" not in result["dependencies"]
    assert "backend" not in result["dependencies"]
    assert result["dependency_groups"]["Runtime"] == ["uvicorn"]
    assert result["dependency_groups"]["Authentication"] == ["jose", "passlib"]
    assert result["dependency_groups"]["Validation"] == ["email_validator", "pydantic"]
    assert result["dependency_groups"]["HTTP Client"] == ["axios"]
    assert result["dependency_groups"]["Python Standard Library"] == [
        "datetime", "json", "re", "typing",
    ]
    assert result["modules"] == ["app/routers/items.py", "main.py"]
    assert result["entry_points"] == ["main.py"]


def test_analysis_infers_layered_fastapi_architecture() -> None:
    files = [
        SimpleNamespace(path="source/app/routers/items.py", language="python", is_entry_point=False, imports=["fastapi"]),
        SimpleNamespace(path="source/app/services/items.py", language="python", is_entry_point=False, imports=[]),
        SimpleNamespace(path="source/app/repositories/items.py", language="python", is_entry_point=False, imports=[]),
    ]

    assert build_dependency_analysis(files)["architecture_style"] == "Layered REST API"
