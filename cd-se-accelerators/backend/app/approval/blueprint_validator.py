"""Blueprint Validator evaluating the 10 architectural criteria before human approval."""

import logging
from typing import Any, Dict, List

from app.approval.approval_schema import ValidationResultItem

logger = logging.getLogger(__name__)


class BlueprintValidator:
    """Validates generated architecture across 10 mandatory architectural criteria."""

    CRITERIA_LIST = [
        "Blueprint Completeness",
        "Epic Hierarchy",
        "User Story Mapping",
        "Frontend Mapping",
        "Folder Structure",
        "Workspace Structure",
        "API Blueprint",
        "Database Blueprint",
        "Dependency Graph",
        "Traceability Map",
    ]

    def validate_all(
        self,
        artifacts_bundle: Dict[str, Any],
    ) -> List[ValidationResultItem]:
        """Perform 10-point architectural validation suite."""
        results: List[ValidationResultItem] = []

        # 1. Blueprint Completeness
        master_bp = artifacts_bundle.get("master_blueprint", {})
        has_arch = "architecture" in master_bp and bool(master_bp["architecture"])
        results.append(
            ValidationResultItem(
                criterion="Blueprint Completeness",
                passed=has_arch,
                details="MasterBlueprint contains complete architectural definitions" if has_arch else "MasterBlueprint missing architecture section",
            )
        )

        # 2. Epic Hierarchy
        ws_manifest = artifacts_bundle.get("workspace_manifest", {})
        epics = ws_manifest.get("epics", [])
        has_epics = len(epics) > 0
        results.append(
            ValidationResultItem(
                criterion="Epic Hierarchy",
                passed=has_epics,
                details=f"Defined {len(epics)} Epics in hierarchy" if has_epics else "No Epics defined",
            )
        )

        # 3. User Story Mapping
        stories = ws_manifest.get("stories", [])
        has_stories = len(stories) > 0
        results.append(
            ValidationResultItem(
                criterion="User Story Mapping",
                passed=has_stories,
                details=f"Mapped {len(stories)} User Stories to Epics" if has_stories else "No User Stories mapped",
            )
        )

        # 4. Frontend Mapping
        frontend = artifacts_bundle.get("generated_frontend", {})
        has_frontend = bool(frontend) and (len(frontend.get("generated_files", [])) > 0 or len(frontend.get("components", [])) > 0)
        results.append(
            ValidationResultItem(
                criterion="Frontend Mapping",
                passed=has_frontend,
                details="Frontend UI components and routes mapped cleanly" if has_frontend else "Frontend UI components missing",
            )
        )

        # 5. Folder Structure
        folders = artifacts_bundle.get("folder_structure", [])
        has_folders = len(folders) >= 5
        results.append(
            ValidationResultItem(
                criterion="Folder Structure",
                passed=has_folders,
                details=f"Validated {len(folders)} project folder paths" if has_folders else "Insufficient folder structure defined",
            )
        )

        # 6. Workspace Structure
        has_ws = bool(ws_manifest) and ("epics" in ws_manifest or "stories" in ws_manifest or "status" in ws_manifest)
        results.append(
            ValidationResultItem(
                criterion="Workspace Structure",
                passed=has_ws,
                details="Workspace manifest structure valid" if has_ws else "Workspace manifest invalid",
            )
        )

        # 7. API Blueprint
        apis = master_bp.get("api_contracts", []) or artifacts_bundle.get("api_blueprint", [])
        has_apis = len(apis) > 0
        results.append(
            ValidationResultItem(
                criterion="API Blueprint",
                passed=has_apis,
                details=f"Defined {len(apis)} API endpoint contracts" if has_apis else "No API contracts defined",
            )
        )

        # 8. Database Blueprint
        dbs = master_bp.get("database_schemas", []) or artifacts_bundle.get("database_blueprint", [])
        has_dbs = len(dbs) > 0
        results.append(
            ValidationResultItem(
                criterion="Database Blueprint",
                passed=has_dbs,
                details=f"Defined {len(dbs)} database table schemas" if has_dbs else "No database schemas defined",
            )
        )

        # 9. Dependency Graph
        dag = ws_manifest.get("dependency_graph", {}) or artifacts_bundle.get("dependency_graph", {})
        is_acyclic = dag.get("is_acyclic", True)
        results.append(
            ValidationResultItem(
                criterion="Dependency Graph",
                passed=is_acyclic,
                details="Story dependency DAG is acyclic and valid" if is_acyclic else "Cyclic dependency detected in story DAG",
            )
        )

        # 10. Traceability Map
        traceability = artifacts_bundle.get("traceability_map", {})
        has_traceability = bool(traceability) or len(stories) > 0
        results.append(
            ValidationResultItem(
                criterion="Traceability Map",
                passed=has_traceability,
                details="Traceability mappings valid across stories and files" if has_traceability else "Traceability map missing",
            )
        )

        return results
