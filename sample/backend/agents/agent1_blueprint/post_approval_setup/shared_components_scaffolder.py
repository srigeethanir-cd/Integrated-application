"""Shared Components Scaffolder — writes additional shared utility files
into outputs/shared/ after the ProjectFolderCreator has run.

This class handles any supplementary shared content that the LLM-driven
ProjectFolderCreator did not cover, and ensures the shared/ directory is
always fully populated.
"""

import json
import os
from typing import Any, Dict, List

from app.utils.logger import get_logger

logger = get_logger(__name__)


class SharedComponentsScaffolder:
    """Supplement the shared/ directory with any missing utility files."""

    def scaffold(
        self,
        project_root: str,
        tech_stack: Dict[str, str],
        shared_components: List[Any],
        modules: List[Dict[str, Any]],
        entities: List[Dict[str, Any]] | None = None,
    ) -> List[str]:
        """Ensure all expected shared files exist, creating any that are missing.

        Args:
            project_root:      Absolute path to the outputs/ directory.
            tech_stack:        Dict with backend/frontend/database/infrastructure.
            shared_components: Shared component list from Agent-1 output.
            modules:           Module list from MasterBlueprint.
            entities:          Entity list from DataModelAnalyzer (optional).

        Returns:
            List of file paths that were created or verified.
        """
        shared_dir = os.path.join(project_root, "shared")
        os.makedirs(shared_dir, exist_ok=True)

        created: List[str] = []
        backend = tech_stack.get("backend", "python").lower()
        use_py = not any(js in backend for js in ("node", "express"))

        if use_py:
            self._ensure_python_shared(shared_dir, modules, entities or [], shared_components, created)
        else:
            self._ensure_js_shared(shared_dir, modules, entities or [], shared_components, created)

        self._ensure_contracts(shared_dir, modules, created)
        self._ensure_component_registry(shared_dir, shared_components, created)

        logger.info("SharedComponentsScaffolder: %d files verified/created", len(created))
        return created

    # ------------------------------------------------------------------
    # Python shared files
    # ------------------------------------------------------------------

    def _ensure_python_shared(self, shared_dir, modules, entities, shared_components, created):
        self._ensure_file(os.path.join(shared_dir, "__init__.py"), "", created)

        self._ensure_file(
            os.path.join(shared_dir, "constants.py"),
            "# Application-wide constants\n\n"
            "DEFAULT_PAGE_SIZE = 20\n"
            "MAX_PAGE_SIZE = 100\n"
            "API_VERSION = 'v1'\n",
            created,
        )

        self._ensure_file(
            os.path.join(shared_dir, "exceptions.py"),
            "class AppError(Exception):\n"
            "    def __init__(self, message: str, code: int = 400):\n"
            "        super().__init__(message)\n"
            "        self.code = code\n\n"
            "class NotFoundError(AppError):\n"
            "    def __init__(self, resource: str):\n"
            "        super().__init__(f'{resource} not found', code=404)\n\n"
            "class ValidationError(AppError):\n"
            "    def __init__(self, detail: str):\n"
            "        super().__init__(f'Validation error: {detail}', code=422)\n\n"
            "class UnauthorizedError(AppError):\n"
            "    def __init__(self):\n"
            "        super().__init__('Unauthorized', code=401)\n",
            created,
        )

        utils_dir = os.path.join(shared_dir, "utils")
        os.makedirs(utils_dir, exist_ok=True)
        self._ensure_file(os.path.join(utils_dir, "__init__.py"), "", created)
        self._ensure_file(
            os.path.join(utils_dir, "logger.py"),
            "import logging, sys\n\n"
            "def get_logger(name: str) -> logging.Logger:\n"
            "    logger = logging.getLogger(name)\n"
            "    if not logger.handlers:\n"
            "        h = logging.StreamHandler(sys.stdout)\n"
            "        h.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s | %(name)s | %(message)s'))\n"
            "        logger.addHandler(h)\n"
            "        logger.setLevel(logging.INFO)\n"
            "    return logger\n",
            created,
        )
        self._ensure_file(
            os.path.join(utils_dir, "pagination.py"),
            "from typing import Any, Dict, List\n\n"
            "def paginate(items: List[Any], page: int = 1, page_size: int = 20) -> Dict[str, Any]:\n"
            "    total = len(items)\n"
            "    start = (page - 1) * page_size\n"
            "    return {'items': items[start:start+page_size], 'total': total, 'page': page,\n"
            "            'page_size': page_size, 'total_pages': (total+page_size-1)//page_size}\n",
            created,
        )

        middleware_dir = os.path.join(shared_dir, "middleware")
        os.makedirs(middleware_dir, exist_ok=True)
        self._ensure_file(os.path.join(middleware_dir, "__init__.py"), "", created)
        self._ensure_file(
            os.path.join(middleware_dir, "auth.py"),
            "def require_auth(request):\n"
            "    token = (request.headers.get('Authorization') or '').replace('Bearer ', '')\n"
            "    if not token:\n"
            "        raise Exception('Missing authorization token')\n"
            "    # TODO: validate JWT\n"
            "    return token\n",
            created,
        )

        types_dir = os.path.join(shared_dir, "types")
        os.makedirs(types_dir, exist_ok=True)
        self._ensure_file(os.path.join(types_dir, "__init__.py"), "", created)

        dto_lines = [
            "from dataclasses import dataclass, field\n"
            "from typing import Any, Dict, Optional\n\n\n"
            "@dataclass\n"
            "class BaseEntity:\n"
            "    id: Optional[str] = None\n"
            "    created_at: Optional[str] = None\n"
            "    updated_at: Optional[str] = None\n\n\n"
        ]
        for entity in entities:
            name = entity.get("name", "Entity").replace(" ", "")
            dto_lines.append(
                f"@dataclass\nclass {name}DTO(BaseEntity):\n"
                f"    # Generated DTO for {name}\n"
                f"    data: Dict[str, Any] = field(default_factory=dict)\n\n\n"
            )
        self._ensure_file(os.path.join(types_dir, "dtos.py"), "".join(dto_lines), created)

    # ------------------------------------------------------------------
    # JavaScript shared files
    # ------------------------------------------------------------------

    def _ensure_js_shared(self, shared_dir, modules, entities, shared_components, created):
        self._ensure_file(
            os.path.join(shared_dir, "constants.js"),
            "module.exports = { DEFAULT_PAGE_SIZE: 20, MAX_PAGE_SIZE: 100, API_VERSION: 'v1' };\n",
            created,
        )
        self._ensure_file(
            os.path.join(shared_dir, "errors.js"),
            "class AppError extends Error {\n"
            "  constructor(message, statusCode = 400) { super(message); this.statusCode = statusCode; }\n"
            "}\n"
            "class NotFoundError extends AppError {\n"
            "  constructor(resource) { super(`${resource} not found`, 404); }\n"
            "}\n"
            "module.exports = { AppError, NotFoundError };\n",
            created,
        )
        utils_dir = os.path.join(shared_dir, "utils")
        os.makedirs(utils_dir, exist_ok=True)
        self._ensure_file(
            os.path.join(utils_dir, "logger.js"),
            "const logger = {\n"
            "  info:  (msg, meta={}) => console.log(JSON.stringify({level:'info',  msg, ...meta})),\n"
            "  error: (msg, meta={}) => console.error(JSON.stringify({level:'error', msg, ...meta})),\n"
            "};\nmodule.exports = logger;\n",
            created,
        )

    # ------------------------------------------------------------------
    # API contracts (language-agnostic JSON)
    # ------------------------------------------------------------------

    def _ensure_contracts(self, shared_dir, modules, created):
        contracts_dir = os.path.join(shared_dir, "contracts")
        os.makedirs(contracts_dir, exist_ok=True)
        for module in modules:
            name = module.get("name", "module")
            safe = name.lower().replace(" ", "_")
            contract_path = os.path.join(contracts_dir, f"{safe}_contract.json")
            if not os.path.exists(contract_path):
                contract = {
                    "module": name,
                    "description": module.get("description", ""),
                    "responsibilities": module.get("responsibilities", []),
                    "endpoints": [
                        {"method": "GET",    "path": f"/api/v1/{safe}"},
                        {"method": "POST",   "path": f"/api/v1/{safe}"},
                        {"method": "GET",    "path": f"/api/v1/{safe}/{{id}}"},
                        {"method": "PUT",    "path": f"/api/v1/{safe}/{{id}}"},
                        {"method": "DELETE", "path": f"/api/v1/{safe}/{{id}}"},
                    ],
                }
                self._ensure_file(contract_path, json.dumps(contract, indent=2) + "\n", created)

    # ------------------------------------------------------------------
    # Component registry
    # ------------------------------------------------------------------

    def _ensure_component_registry(self, shared_dir, shared_components, created):
        registry_path = os.path.join(shared_dir, "component_registry.json")
        if not os.path.exists(registry_path):
            self._ensure_file(
                registry_path,
                json.dumps({"shared_components": shared_components}, indent=2) + "\n",
                created,
            )

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    @staticmethod
    def _ensure_file(path: str, content: str, log: List[str]) -> None:
        """Write file only if it does not already exist."""
        if not os.path.exists(path):
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(content)
        log.append(path)
