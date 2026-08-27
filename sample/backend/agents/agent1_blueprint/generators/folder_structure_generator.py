from typing import Any, Dict, List

class FolderStructureGenerator:
    """Generate a folder structure blueprint (JSON) based on the project configuration."""

    def generate(self, project_config: Dict[str, Any], modules: List[Dict[str, Any]]) -> Dict[str, Any]:
        project_name = project_config.get("project_name", "generated_project")
        tech_stack = project_config.get("tech_stack", {})
        backend_tech = tech_stack.get("backend", "python").lower()
        frontend_tech = tech_stack.get("frontend", "react").lower()

        # Let's outline the files and folders to create
        folders = ["backend", "frontend", "shared", "workspace", "metadata"]
        files = []

        # Backend files based on technology
        if "fastapi" in backend_tech:
            files.extend([
                {"path": "backend/main.py", "template_key": "fastapi_main"},
                {"path": "backend/requirements.txt", "template_key": "fastapi_reqs"},
                {"path": "backend/config.py", "template_key": "fastapi_config"},
            ])
        elif "django" in backend_tech:
            files.extend([
                {"path": "backend/manage.py", "template_key": "django_manage"},
                {"path": "backend/requirements.txt", "template_key": "django_reqs"},
                {"path": "backend/app/__init__.py", "template_key": "empty"},
                {"path": "backend/app/settings.py", "template_key": "django_settings"},
            ])
        elif "flask" in backend_tech:
            files.extend([
                {"path": "backend/app.py", "template_key": "flask_app"},
                {"path": "backend/requirements.txt", "template_key": "flask_reqs"},
                {"path": "backend/config.py", "template_key": "flask_config"},
            ])
        elif "node" in backend_tech or "express" in backend_tech:
            files.extend([
                {"path": "backend/index.js", "template_key": "express_main"},
                {"path": "backend/package.json", "template_key": "express_package"},
                {"path": "backend/.env.example", "template_key": "express_env"},
            ])
        else: # Default python
            files.extend([
                {"path": "backend/main.py", "template_key": "python_main"},
                {"path": "backend/requirements.txt", "template_key": "python_reqs"},
                {"path": "backend/config.py", "template_key": "python_config"},
            ])

        # Create module folders and files in backend
        use_py = not any(js in backend_tech for js in ("node", "express"))
        for m in modules:
            m_name = m.get("name", "module").lower().replace(" ", "_")
            m_folder = f"backend/{m_name}"
            if m_folder not in folders:
                folders.append(m_folder)
            if use_py:
                files.extend([
                    {"path": f"{m_folder}/__init__.py", "template_key": "empty"},
                    {"path": f"{m_folder}/service.py", "template_key": "python_service", "module_name": m.get("name")},
                    {"path": f"{m_folder}/models.py", "template_key": "python_models", "module_name": m.get("name")},
                    {"path": f"{m_folder}/routes.py", "template_key": "python_routes", "module_name": m.get("name")},
                ])
            else:
                files.extend([
                    {"path": f"{m_folder}/{m_name}.controller.js", "template_key": "js_controller", "module_name": m.get("name")},
                    {"path": f"{m_folder}/{m_name}.service.js", "template_key": "js_service", "module_name": m.get("name")},
                    {"path": f"{m_folder}/{m_name}.routes.js", "template_key": "js_routes", "module_name": m.get("name")},
                ])

        # Frontend files based on technology
        if "react" in frontend_tech:
            for ff in ["frontend/public", "frontend/src", "frontend/src/components", "frontend/src/pages"]:
                if ff not in folders:
                    folders.append(ff)
            files.extend([
                {"path": "frontend/package.json", "template_key": "react_package"},
                {"path": "frontend/src/App.jsx", "template_key": "react_app"},
                {"path": "frontend/src/index.jsx", "template_key": "react_index"},
                {"path": "frontend/public/index.html", "template_key": "react_html"},
            ])
        elif "vue" in frontend_tech:
            for ff in ["frontend/src", "frontend/src/components"]:
                if ff not in folders:
                    folders.append(ff)
            files.extend([
                {"path": "frontend/package.json", "template_key": "vue_package"},
                {"path": "frontend/src/App.vue", "template_key": "vue_app"},
                {"path": "frontend/src/main.js", "template_key": "vue_main"},
            ])
        elif "angular" in frontend_tech:
            for ff in ["frontend/src", "frontend/src/app"]:
                if ff not in folders:
                    folders.append(ff)
            files.extend([
                {"path": "frontend/package.json", "template_key": "angular_package"},
                {"path": "frontend/src/app/app.component.ts", "template_key": "angular_component"},
                {"path": "frontend/src/app/app.module.ts", "template_key": "angular_module"},
            ])
        elif "next" in frontend_tech:
            for ff in ["frontend/pages", "frontend/components"]:
                if ff not in folders:
                    folders.append(ff)
            files.extend([
                {"path": "frontend/package.json", "template_key": "next_package"},
                {"path": "frontend/pages/index.jsx", "template_key": "next_index"},
                {"path": "frontend/pages/_app.jsx", "template_key": "next_app"},
            ])

        # Shared files
        for sf in ["shared/contracts", "shared/utils", "shared/types", "shared/middleware"]:
            if sf not in folders:
                folders.append(sf)
        files.extend([
            {"path": "shared/README.md", "template_key": "shared_readme"},
            {"path": ".env.example", "template_key": "env_example"},
            {"path": "README.md", "template_key": "readme"},
        ])

        return {
            "project_name": project_name,
            "folders": folders,
            "files": files,
        }
