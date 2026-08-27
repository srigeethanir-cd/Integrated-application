"""Navigation Generator producing menu items, breadcrumbs, and sidebar structures."""

import logging
from typing import Any, Dict, List
from pydantic import BaseModel, Field

from agents.agent0_wireframe.screen_detector import DetectedScreen

logger = logging.getLogger(__name__)


class NavItem(BaseModel):
    """Navigation menu item definition."""

    id: str = Field(description="Unique navigation item ID")
    label: str = Field(description="Display label string")
    path: str = Field(description="Target route path")
    icon: str = Field(default="LayoutDashboard", description="Lucide-react icon name")
    is_active_default: bool = Field(default=False, description="Whether selected by default")


class NavigationGenerator:
    """Generates navigation structures for sidebar menus, top headers, and breadcrumbs."""

    def generate_navigation(self, screens: List[DetectedScreen]) -> Dict[str, Any]:
        """Generate structured navigation config for the React TypeScript frontend."""
        nav_items: List[NavItem] = []

        icon_map = {
            "dashboard": "LayoutDashboard",
            "form": "FileText",
            "table": "Table",
            "login": "LogIn",
            "settings": "Settings",
        }

        for idx, screen in enumerate(screens):
            nav_items.append(
                NavItem(
                    id=screen.screen_id,
                    label=screen.name,
                    path=screen.route_path,
                    icon=icon_map.get(screen.screen_type, "Box"),
                    is_active_default=(idx == 0),
                )
            )

        return {
            "sidebar_menu": [n.model_dump() for n in nav_items],
            "header_actions": [
                {"id": "ACT_NOTIF", "label": "Notifications", "icon": "Bell"},
                {"id": "ACT_PROFILE", "label": "Profile", "icon": "User"},
            ],
            "breadcrumbs": [
                {"label": "Home", "path": "/"},
            ],
        }
