import os
from typing import Any, Dict, List

class ReviewReportGenerator:
    """Generate a clean, human-readable Architecture Review report from the generated blueprints."""

    def generate(
        self,
        project_manifest: Dict[str, Any],
        master_blueprint: Dict[str, Any],
        implementation_plan: Dict[str, Any],
        shared_components: List[Dict[str, Any]],
        folder_blueprint: Dict[str, Any],
        api_contracts: Dict[str, Any],
        database_blueprint: Dict[str, Any],
        dependency_blueprint: Dict[str, Any],
    ) -> str:
        project_name = project_manifest.get("project_name", "Generated Project")
        tech_stack = project_manifest.get("tech_stack", {})
        
        lines = [
            f"# Architecture Review Report: {project_name}",
            "",
            "## Project Summary",
            project_manifest.get("description", "No description provided."),
            "",
            "## Technology Stack",
            f"- **Backend**: {tech_stack.get('backend', 'python').capitalize()}",
            f"- **Frontend**: {tech_stack.get('frontend', 'react').capitalize()}",
            f"- **Database**: {tech_stack.get('database', 'postgresql').capitalize()}",
            f"- **Framework / Infra**: {tech_stack.get('infrastructure', 'docker').capitalize()}",
            "",
            "## Modules",
        ]

        # Add modules
        for mod in master_blueprint.get("modules", []):
            mod_name = mod.get("name", "Unnamed Module")
            lines.extend([
                f"### {mod_name}",
                f"- **Purpose**: {mod.get('description', 'No purpose specified.')}",
                f"- **Responsibilities**: {', '.join(mod.get('responsibilities', []))}",
            ])
            # Find dependencies for this module
            deps = []
            for dep in dependency_blueprint.get("dependencies", []):
                source_basename = os.path.basename(dep["source"])
                mod_safe = mod_name.lower().replace(" ", "_")
                if source_basename == mod_safe:
                    target_name = os.path.basename(dep["target"])
                    deps.append(f"{target_name} ({dep['type']})")
            if deps:
                lines.append(f"- **Dependencies**: {', '.join(deps)}")
            lines.append("")

        # Shared Components
        lines.extend([
            "## Shared Components",
            "Cross-cutting concerns implemented in the shared folder:",
        ])
        for comp in shared_components:
            lines.append(f"- **{comp['name']}** (Owner: {comp.get('owner', 'shared')})")
        lines.append("")

        # Folder Structure
        lines.extend([
            "## Project Folder Structure",
            "```text",
            f"{project_name.lower().replace(' ', '_')}/",
            "  backend/       # Server application",
            "  frontend/      # Client interface",
            "  shared/        # Shared assets and utilities",
            "  workspace/     # Sandbox development folder",
            "  metadata/      # Project build metadata",
            "```",
            "",
            "### Backend Folder Structure",
            "```text",
            "backend/",
        ])
        # List backend folders
        backend_folders = [f for f in folder_blueprint.get("folders", []) if f.startswith("backend/")]
        for bf in sorted(backend_folders):
            parts = bf.split("/")
            indent = "  " * (len(parts) - 1)
            lines.append(f"{indent}{parts[-1]}/")
        lines.extend([
            "```",
            "",
            "### Frontend Folder Structure",
            "```text",
            "frontend/",
        ])
        # List frontend folders
        frontend_folders = [f for f in folder_blueprint.get("folders", []) if f.startswith("frontend/")]
        for ff in sorted(frontend_folders):
            parts = ff.split("/")
            indent = "  " * (len(parts) - 1)
            lines.append(f"{indent}{parts[-1]}/")
        lines.extend([
            "```",
            "",
            "## Database Summary",
            f"Database type: **{database_blueprint.get('database_type', 'postgresql')}**",
            "",
            "Tables & Columns:",
        ])
        for table in database_blueprint.get("tables", []):
            col_strs = []
            for col in table["columns"]:
                col_type = col["type"]
                col_extra = []
                if col.get("primary_key"):
                    col_extra.append("PK")
                if col.get("unique"):
                    col_extra.append("Unique")
                if col.get("foreign_key"):
                    col_extra.append(f"FK -> {col['foreign_key']}")
                extra_str = f" ({', '.join(col_extra)})" if col_extra else ""
                col_strs.append(f"{col['name']}: `{col_type}`{extra_str}")
            lines.extend([
                f"- **{table['name']}** table:",
                f"  - Columns: {', '.join(col_strs)}"
            ])
        lines.append("")

        # API Summary
        lines.extend([
            "## API Summary",
            "Defined API Routes:",
        ])
        for contract in api_contracts.get("contracts", []):
            lines.append(f"### {contract['module']} Endpoints")
            for ep in contract.get("endpoints", []):
                lines.append(f"- `{ep['method']}` `{ep['path']}`: {ep['description']}")
            lines.append("")

        # Implementation Phases
        lines.extend([
            "## Implementation Phases",
        ])
        for phase in implementation_plan.get("phases", []):
            lines.extend([
                f"### Phase: {phase['phase']}",
                f"- **Goal**: {phase['goal']}",
                f"- **Deliverables**: {', '.join(phase['deliverables'])}",
                ""
            ])

        # Estimated Project Metrics
        lines.extend([
            "## Estimated Project Metrics",
            f"- **Estimated Modules**: {len(master_blueprint.get('modules', []))}",
            f"- **Estimated Database Tables**: {len(database_blueprint.get('tables', []))}",
            f"- **Estimated API Endpoints**: {sum(len(c.get('endpoints', [])) for c in api_contracts.get('contracts', []))}",
            f"- **Story Count**: {project_manifest.get('story_count', 0)}",
            "",
            "---",
            "",
            "Approving this blueprint will create the project skeleton and hand over the project to Agent-2.",
            ""
        ])

        return "\n".join(lines)
