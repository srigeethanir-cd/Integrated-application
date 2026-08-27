"""Responsive Layout Generator for Agent 0.

Computes responsive layout classes, tailwind breakpoint mappings, aspect ratio preservation rules, and responsive_metadata.json.
"""

import os
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ResponsiveGenerator:
    """Generates responsive styles, media query wrappers, and responsive device metadata maps."""

    def __init__(self, output_dir: str = "workspace/generator"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_responsive_metadata(self, image_path: str, layout_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Compute grid, flex, and spacing changes across mobile, tablet, laptop, and ultra-wide screens."""
        logger.info("ResponsiveGenerator: Commencing multi-device responsive class mapping on: %s", image_path)

        breakpoints = {
            "mobile": {"min_width": "320px", "columns": 1, "padding": "12px", "gap": "8px"},
            "tablet": {"min_width": "768px", "columns": 2, "padding": "16px", "gap": "12px"},
            "laptop": {"min_width": "1024px", "columns": 3, "padding": "20px", "gap": "16px"},
            "desktop": {"min_width": "1440px", "columns": 4, "padding": "24px", "gap": "20px"},
            "ultrawide": {"min_width": "1920px", "columns": 6, "padding": "32px", "gap": "24px"}
        }

        responsive_metadata = {
            "breakpoints": breakpoints,
            "element_mappings": {
                "SCREEN_CONTAINER": {
                    "classes": "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 p-4 lg:p-6"
                },
                "AUTH_CARD": {
                    "classes": "w-full max-w-sm md:max-w-md mx-auto my-4 p-6 md:p-8"
                },
                "SIDEBAR": {
                    "classes": "hidden lg:block lg:w-64 bg-slate-800 border-r border-slate-700"
                }
            }
        }

        # Write responsive_metadata.json directly
        with open(self.output_dir / "responsive_metadata.json", "w", encoding="utf-8") as f:
            json.dump(responsive_metadata, f, indent=2)

        return responsive_metadata
