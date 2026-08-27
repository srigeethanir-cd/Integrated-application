"""Frontend Analyzer for Agent 2.

Analyzes Agent 0 generated frontend components, routes, and API expectations before generating backend functionality.
"""

import logging
import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class FrontendContractSpec(BaseModel):
    """Specification of frontend components, routes, and expected backend API contracts."""

    existing_components: List[str] = Field(default_factory=list, description="Existing component names")
    existing_pages: List[str] = Field(default_factory=list, description="Existing page component names")
    expected_endpoints: List[Dict[str, str]] = Field(default_factory=list, description="Expected API endpoints and methods")
    form_fields: List[str] = Field(default_factory=list, description="Expected form fields")


class FrontendAnalyzer:
    """Analyzes generated frontend code artifacts from Agent 0 to ensure backend API contract alignment."""

    def analyze_frontend(
        self,
        generated_frontend_files: List[Dict[str, Any]],
        ui_metadata: Optional[Dict[str, Any]] = None,
    ) -> FrontendContractSpec:
        """Inspect frontend files and extract expected API routes and component structures."""
        components = []
        pages = []
        endpoints = []
        fields = []

        for f in generated_frontend_files:
            path = f.get("path", "")
            content = f.get("content", "")

            if "pages/" in path:
                filename = path.split("/")[-1].replace(".tsx", "").replace(".jsx", "")
                pages.append(filename)

                # Extract fetch or axios API URLs
                matches = re.findall(r"fetch\(['\"]([^'\"]+)['\"]", content)
                for m in matches:
                    endpoints.append({"endpoint": m, "method": "GET/POST"})

                # Extract form fields
                field_matches = re.findall(r"name=['\"]([^'\"]+)['\"]", content)
                fields.extend(field_matches)

            elif "components/" in path:
                filename = path.split("/")[-1].replace(".tsx", "").replace(".jsx", "")
                components.append(filename)

        if not endpoints:
            endpoints.append({"endpoint": "/api/v1/resource", "method": "GET"})

        return FrontendContractSpec(
            existing_components=components,
            existing_pages=pages,
            expected_endpoints=endpoints,
            form_fields=list(set(fields)),
        )
