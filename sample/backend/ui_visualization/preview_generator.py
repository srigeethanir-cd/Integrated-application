import os
import json
import shutil
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List

class PreviewGenerator:
    """Generates preview metadata, screenshots, and execution timeline records."""

    def generate_timeline(self, story_key: str, status: str = "completed") -> Dict[str, Any]:
        """Generate simulated or logged execution timeline events."""
        now = datetime.now(timezone.utc).isoformat()
        return {
            "story_key": story_key,
            "status": status,
            "events": [
                {"timestamp": now, "agent": "Agent0", "event": "Wireframe specifications analyzed"},
                {"timestamp": now, "agent": "Agent1", "event": "Architectural blueprints generated"},
                {"timestamp": now, "agent": "Agent2", "event": "Isolated backend and frontend code generated"},
                {"timestamp": now, "agent": "ValidationEngine", "event": "Completed local sandbox validation checks"}
            ]
        }

    def generate_preview_files(self, output_path: Path):
        """Generate static asset placeholders or templates for frontend previews."""
        preview_dir = output_path / "preview_assets"
        screenshots_dir = output_path / "screenshots"
        
        preview_dir.mkdir(parents=True, exist_ok=True)
        screenshots_dir.mkdir(parents=True, exist_ok=True)

        # Write dummy screenshot metadata or copy if any screenshot exists
        with open(preview_dir / "index.html", "w", encoding="utf-8") as f:
            f.write("<!DOCTYPE html><html><body><h1>Application Component Live View</h1></body></html>")
            
        with open(screenshots_dir / "meta.json", "w", encoding="utf-8") as f:
            json.dump({"screenshots": ["mock_view.png"]}, f, indent=2)
