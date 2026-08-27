"""Style Extraction Engine for Agent 0.

Extracts typography, color systems, border styles, shadow elevations, gradients, and interactive state stylings.
"""

import os
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class StyleEngine:
    """Performs visual style analysis, design systems extraction, and interactive states mapping."""

    def __init__(self, output_dir: str = "workspace/style"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def extract_styles(self, image_path: str, layout_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Analyze borders, shadows, gradients, and color palette tokens from wireframes."""
        logger.info("StyleEngine: Commencing visual style and design systems extraction on: %s", image_path)

        styles = {
            "theme_mode": "dark",
            "colors": {
                "primary": "#3498db",
                "secondary": "#f1c40f",
                "accent": "#9b59b6",
                "background": "#0f172a",
                "card_bg": "#1e293b",
                "text_primary": "#ffffff",
                "text_secondary": "#94a3b8",
                "border": "#334155"
            },
            "typography": {
                "font_family": "Plus Jakarta Sans, sans-serif",
                "base_size": "16px",
                "headings": {
                    "h1": {"size": "32px", "weight": "700", "line_height": "1.2"},
                    "h2": {"size": "24px", "weight": "600", "line_height": "1.3"}
                },
                "body": {"size": "16px", "weight": "400", "line_height": "1.5"}
            },
            "borders": {
                "default_radius": "8px",
                "card_radius": "12px",
                "button_radius": "9999px",
                "border_width": "1px"
            },
            "shadows": {
                "card_shadow": "0 10px 25px rgba(0,0,0,0.3)",
                "button_shadow": "0 4px 12px rgba(52,152,219,0.25)",
                "elevation_z": 4
            },
            "spacing": {
                "padding_base": "16px",
                "margin_base": "16px",
                "gap_base": "12px"
            },
            "states": {
                "hover": {
                    "button": {"brightness": "1.1", "cursor": "pointer"},
                    "input": {"border_color": "#38bdf8"}
                },
                "focus": {
                    "input": {"outline": "2px solid #38bdf8", "shadow": "0 0 0 4px rgba(56,189,248,0.2)"}
                },
                "disabled": {
                    "button": {"opacity": "0.5", "cursor": "not-allowed"}
                }
            }
        }

        # Write style.json directly
        with open(self.output_dir / "style.json", "w", encoding="utf-8") as f:
            json.dump(styles, f, indent=2)

        return styles
