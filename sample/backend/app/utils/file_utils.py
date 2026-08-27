"""File system and format helper utilities."""

import json
import os
import shutil
from pathlib import Path
from typing import Any, Dict, Optional, Union

try:
    import yaml
except ImportError:
    yaml = None


def ensure_dir(dir_path: Union[str, Path]) -> Path:
    """Ensure a directory path exists, creating parents if missing."""
    path = Path(dir_path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def read_json_file(file_path: Union[str, Path], default: Optional[Any] = None) -> Any:
    """Read and parse a JSON file with optional fallback default."""
    path = Path(file_path)
    if not path.exists():
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json_file(file_path: Union[str, Path], data: Any, indent: int = 2) -> Path:
    """Safely write data to a JSON file, creating parent directories."""
    path = Path(file_path)
    ensure_dir(path.parent)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)
    return path


def read_yaml_file(file_path: Union[str, Path], default: Optional[Any] = None) -> Any:
    """Read and parse a YAML file."""
    if yaml is None:
        raise RuntimeError("PyYAML is not installed.")
    path = Path(file_path)
    if not path.exists():
        return default
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def write_yaml_file(file_path: Union[str, Path], data: Any) -> Path:
    """Write data to a YAML file."""
    if yaml is None:
        raise RuntimeError("PyYAML is not installed.")
    path = Path(file_path)
    ensure_dir(path.parent)
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False)
    return path


def safe_delete_dir(dir_path: Union[str, Path]) -> bool:
    """Recursively delete a directory if it exists."""
    path = Path(dir_path)
    if path.exists() and path.is_dir():
        shutil.rmtree(path)
        return True
    return False


async def save_upload_file(upload_file, destination_folder: str = "uploads") -> str:
    """Save an UploadFile to a local destination directory."""
    dest = ensure_dir(destination_folder) / upload_file.filename
    content = await upload_file.read()
    with open(dest, "wb") as f:
        f.write(content)
    return str(dest)
