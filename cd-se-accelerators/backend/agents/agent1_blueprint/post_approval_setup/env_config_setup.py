import os
from typing import Any, Dict

class EnvConfigSetup:
    """Post-approval setup to dynamically create .env configuration files."""

    def setup_env(self, project_root: str, project_name: str, tech_stack: Dict[str, str]) -> str:
        """Create the .env configuration file under project_root."""
        env_path = os.path.join(project_root, ".env")
        db_type = tech_stack.get("database", "postgresql").lower()
        safe_name = "".join(c for c in project_name if c.isalnum() or c in ("-", "_")).lower()

        if "postgres" in db_type:
            db_url = f"postgresql://user:password@localhost:5432/{safe_name}"
        elif "mysql" in db_type:
            db_url = f"mysql://user:password@localhost:3306/{safe_name}"
        elif "mongo" in db_type:
            db_url = f"mongodb://localhost:27017/{safe_name}"
        else:
            db_url = f"sqlite:///sqlite.db"

        env_lines = [
            f"# Dynamic environment configurations for {project_name}",
            f"PROJECT_NAME={project_name}",
            f"DATABASE_URL={db_url}",
            f"SECRET_KEY=generate-key-placeholder",
            f"DEBUG=true",
        ]

        with open(env_path, "w", encoding="utf-8") as handle:
            handle.write("\n".join(env_lines) + "\n")

        return env_path
