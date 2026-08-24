"""Component Mapper generating unified component trees, component_map.json, and ui_metadata.json."""

import json
import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from agents.agent0_wireframe.screen_detector import DetectedScreen
from agents.agent0_wireframe.wireframe_analyzer import FunctionalUISpec, VisualUISpec

logger = logging.getLogger(__name__)


class UnifiedComponent(BaseModel):
    """Unified React component model linking visual and functional specifications."""

    component_id: str = Field(description="Unique component identifier (e.g. COMP_HEADER)")
    name: str = Field(description="React component class/function name (e.g. HeaderNav)")
    category: str = Field(description="Category: layout | form | navigation | display | feedback")
    behavior: str = Field(description="Client-side functional behavior and state handlers")
    visual_details: str = Field(description="Styling guidelines, box model, colors, and OCR text")
    requires_state: bool = Field(default=False, description="Whether state hook (useState) is required")
    children: List[str] = Field(default_factory=list, description="Child component names")


class ComponentMapper:
    """Maps visual UI elements and functional specs into unified component maps for downstream consumption."""

    def build_component_map(
        self,
        screens: List[DetectedScreen],
        visual_spec: VisualUISpec,
        functional_spec: FunctionalUISpec,
    ) -> Dict[str, Any]:
        """Generate structured component_map.json and ui_metadata payload."""
        components: List[UnifiedComponent] = []

        # Core Layout Components
        components.append(
            UnifiedComponent(
                component_id="COMP_HEADER",
                name="HeaderNavbar",
                category="layout",
                behavior="Renders application logo, page title, user avatar, and navigation toggles",
                visual_details=f"Top fixed header bar, background {visual_spec.color_palette[0] if visual_spec.color_palette else '#0f172a'}, flex alignment",
                requires_state=True,
            )
        )
        components.append(
            UnifiedComponent(
                component_id="COMP_SIDEBAR",
                name="SidebarNav",
                category="navigation",
                behavior="Collapsible sidebar navigation menu with active route highlighting",
                visual_details="Left vertical panel, responsive toggle on mobile (<768px)",
                requires_state=True,
            )
        )
        components.append(
            UnifiedComponent(
                component_id="COMP_FOOTER",
                name="AppFooter",
                category="layout",
                behavior="Displays copyright, version info, and system status links",
                visual_details="Bottom footer panel with muted typography",
                requires_state=False,
            )
        )

        # Dynamic Screen Components
        for screen in screens:
            comp_id = f"COMP_{screen.component_name.upper()}"
            category = "display"
            if screen.screen_type == "form":
                category = "form"
            elif screen.screen_type == "login":
                category = "form"

            components.append(
                UnifiedComponent(
                    component_id=comp_id,
                    name=screen.component_name,
                    category=category,
                    behavior=f"Renders {screen.name} page view with interactive state and data bindings",
                    visual_details=f"Screen layout for {screen.name} utilizing flex grid container",
                    requires_state=True,
                )
            )

        # Functional Components
        for idx, feat in enumerate(functional_spec.core_features):
            safe_name = "".join([w.capitalize() for w in feat.name.split() if w.isalnum()]) or f"FeatureComp{idx+1}"
            components.append(
                UnifiedComponent(
                    component_id=f"COMP_FEAT_{idx+1}",
                    name=safe_name,
                    category="display",
                    behavior=feat.behavior,
                    visual_details="Card container with responsive padding",
                    requires_state=True,
                )
            )

        component_map = {
            "meta": {
                "generator": "Agent-0 Wireframe Component Mapper",
                "screen_count": len(screens),
                "component_count": len(components),
            },
            "screens": [s.model_dump() for s in screens],
            "components": [c.model_dump() for c in components],
            "ui_metadata": {
                "color_palette": visual_spec.color_palette,
                "layout_structure": visual_spec.layout_structure,
                "responsive_hints": visual_spec.responsive_hints,
                "state_elements": functional_spec.state_management,
                "mock_data": functional_spec.data_payload,
            },
        }

        return component_map
