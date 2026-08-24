import os
from pathlib import Path
from typing import Dict, Any

class FolderTreeVisualizer:
    """Generates recursive folder tree representation in JSON format."""

    def generate_tree(self, root_path: Path) -> Dict[str, Any]:
        """Walk root_path recursively and build a nested tree structure."""
        if not root_path.exists():
            return {"name": root_path.name, "type": "directory", "children": []}

        name = root_path.name
        if root_path.is_file():
            return {
                "name": name,
                "type": "file",
                "size_bytes": root_path.stat().st_size
            }

        children = []
        try:
            for item in sorted(root_path.iterdir(), key=lambda x: (not x.is_dir(), x.name)):
                if item.name in (".git", "__pycache__", "node_modules", ".venv", "venv", ".gemini"):
                    continue
                children.append(self.generate_tree(item))
        except Exception:
            pass

        return {
            "name": name,
            "type": "directory",
            "children": children
        }
