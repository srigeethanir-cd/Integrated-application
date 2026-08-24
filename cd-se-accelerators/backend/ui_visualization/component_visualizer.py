import os
import re
from pathlib import Path
from typing import Dict, Any, List

class ComponentVisualizer:
    """Scans TSX/JSX files to build UI component hierarchies."""

    def scan_components(self, frontend_path: Path) -> Dict[str, Any]:
        """Scan React components inside frontend_path and build tree/hierarchy."""
        components = []
        if not frontend_path.exists():
            return {"name": "Root", "children": []}

        tsx_files = list(frontend_path.glob("**/*.tsx")) + list(frontend_path.glob("**/*.jsx"))
        
        for f in tsx_files:
            try:
                with open(f, "r", encoding="utf-8", errors="ignore") as file_obj:
                    content = file_obj.read()
                
                comp_name = f.stem
                # Simple regex checks to identify component details
                imports = re.findall(r'import\s+.*?\s+from\s+["\'](.*?)["\']', content)
                props = re.findall(r'interface\s+(\w+Props)\s*\{', content)
                
                components.append({
                    "name": comp_name,
                    "file_path": str(f.name),
                    "props": props[0] if props else "any",
                    "imports": [imp for imp in imports if imp.startswith((".", "@"))]
                })
            except Exception:
                pass

        return {
            "name": "Frontend Components",
            "type": "hierarchy",
            "children": components
        }
