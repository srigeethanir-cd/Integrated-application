"""Screen Detector for identifying distinct application screens and pages from wireframe specs."""

import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class DetectedScreen(BaseModel):
    """Model representing a detected application screen/page."""

    screen_id: str = Field(description="Unique screen ID (e.g. SCREEN_DASHBOARD)")
    name: str = Field(description="Display screen title (e.g. Dashboard Page)")
    route_path: str = Field(description="URL route path (e.g. /dashboard)")
    screen_type: str = Field(description="Type: dashboard | form | table | detail | login | settings")
    component_name: str = Field(description="React TSX component name (e.g. DashboardPage)")
    description: str = Field(description="Screen responsibility and key interactive elements")


class ScreenDetector:
    """Detects and categorizes application pages and screens from wireframes and user stories."""

    def detect_screens(
        self,
        stories: List[Dict[str, Any]],
        visual_spec: Optional[Any] = None,
    ) -> List[DetectedScreen]:
        """Detect and register all application screens from user stories and visual wireframes."""
        screens: List[DetectedScreen] = []

        if not stories:
            # Default fallback application screens
            return [
                DetectedScreen(
                    screen_id="SCREEN_DASHBOARD",
                    name="Dashboard",
                    route_path="/",
                    screen_type="dashboard",
                    component_name="DashboardPage",
                    description="Overview dashboard with key metrics and action shortcuts",
                ),
                DetectedScreen(
                    screen_id="SCREEN_LOGIN",
                    name="Login",
                    route_path="/login",
                    screen_type="login",
                    component_name="LoginPage",
                    description="User authentication and sign in screen",
                ),
            ]

        seen_routes = set()

        for idx, story in enumerate(stories):
            title = story.get("title") or story.get("name") or f"Screen {idx + 1}"
            story_key = story.get("story_key") or story.get("id") or f"US{idx + 1}"

            # Infer route path and screen type
            slug = title.lower().replace(" ", "-").replace("page", "").strip("-")
            route_path = f"/{slug}" if slug and slug != "home" else "/"
            if route_path in seen_routes:
                route_path = f"/{slug}-{idx + 1}"
            seen_routes.add(route_path)

            screen_type = "form"
            if "dashboard" in title.lower() or "overview" in title.lower():
                screen_type = "dashboard"
            elif "list" in title.lower() or "table" in title.lower() or "view" in title.lower():
                screen_type = "table"
            elif "login" in title.lower() or "auth" in title.lower():
                screen_type = "login"
            elif "setting" in title.lower():
                screen_type = "settings"

            comp_words = [w.capitalize() for w in title.replace("-", " ").split() if w.isalnum()]
            comp_name = "".join(comp_words)
            if not comp_name.endswith("Page"):
                comp_name += "Page"

            screens.append(
                DetectedScreen(
                    screen_id=f"SCREEN_{story_key.upper()}",
                    name=title,
                    route_path=route_path,
                    screen_type=screen_type,
                    component_name=comp_name,
                    description=story.get("description", f"Screen for {title}"),
                )
            )

        return screens
