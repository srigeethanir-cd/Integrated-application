import os
import re
from pathlib import Path
from typing import Dict, Any, List

class ApiVisualizer:
    """Scans Python API routers to extract endpoints and build API graphs."""

    def generate_api_graph(self, backend_path: Path) -> Dict[str, Any]:
        """Scan python files for router decorator definitions."""
        endpoints = []
        if not backend_path.exists():
            return {"endpoints": []}

        router_files = list(backend_path.glob("**/*router.py")) + list(backend_path.glob("**/routes/**/*.py"))
        route_pattern = re.compile(r'@router\.(get|post|put|delete|patch)\(\s*["\'](.*?)["\']')

        for f in router_files:
            try:
                with open(f, "r", encoding="utf-8", errors="ignore") as file_obj:
                    content = file_obj.read()
                
                matches = route_pattern.findall(content)
                for method, path in matches:
                    endpoints.append({
                        "method": method.upper(),
                        "path": path,
                        "file": f.name,
                        "tags": [f.stem.replace("_router", "").replace("router", "")]
                    })
            except Exception:
                pass

        return {
            "endpoints": endpoints,
            "total_endpoints": len(endpoints)
        }
