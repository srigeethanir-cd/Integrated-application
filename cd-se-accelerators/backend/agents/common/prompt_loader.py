"""Prompt loader utility for loading and rendering agent prompt templates."""

import os
from pathlib import Path
from typing import Any, Dict, Optional

try:
    from jinja2 import Template
except ImportError:
    Template = None


class PromptLoader:
    """Utility for loading and rendering prompt templates from disk or memory."""

    def __init__(self, prompts_dir: Optional[str] = None):
        self.prompts_dir = Path(prompts_dir or "backend/prompts")

    def load_prompt(self, prompt_name: str) -> str:
        """Load a prompt file from disk or PostgreSQL database template."""
        # Convert prompt_name to unique prompt_code
        prompt_code = prompt_name.replace("/", "_").replace("\\", "_").replace(".", "_")
        
        from app.database.session import SessionLocal
        from app.models.prompt_template import PromptTemplate
        
        db = SessionLocal()
        try:
            db_template = db.query(PromptTemplate).filter_by(prompt_code=prompt_code, is_active=True).first()
            if db_template:
                return db_template.prompt_template
        except Exception:
            pass
        finally:
            db.close()

        if not prompt_name.endswith((".txt", ".md", ".prompt")):
            possible_paths = [
                self.prompts_dir / f"{prompt_name}.txt",
                self.prompts_dir / f"{prompt_name}.md",
                self.prompts_dir / f"{prompt_name}.prompt",
            ]
        else:
            possible_paths = [self.prompts_dir / prompt_name]

        disk_content = None
        for path in possible_paths:
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    disk_content = f.read()
                    break

        if disk_content is None:
            disk_content = f"System Prompt for {prompt_name}"

        # Seed the DB with this content if not exists
        db = SessionLocal()
        try:
            db_template = db.query(PromptTemplate).filter_by(prompt_code=prompt_code).first()
            if not db_template:
                from app.repository.prompt_template_repository import PromptTemplateRepository
                repo = PromptTemplateRepository(db)
                repo.create_template({
                    "prompt_code": prompt_code,
                    "prompt_name": prompt_name,
                    "description": f"Auto-seeded prompt template for {prompt_name}",
                    "agent_name": prompt_name.split("/")[0] if "/" in prompt_name else "common",
                    "prompt_template": disk_content,
                    "status": "Approved",
                    "is_active": True
                })
        except Exception:
            pass
        finally:
            db.close()

        return disk_content

    def render_prompt(self, template_str: str, variables: Dict[str, Any]) -> str:
        """Render a prompt template with variables."""
        if Template is not None:
            template = Template(template_str)
            return template.render(**variables)
        else:
            # Fallback basic string replacement
            result = template_str
            for key, val in variables.items():
                result = result.replace(f"{{{{ {key} }}}}", str(val)).replace(f"{{{key}}}", str(val))
            return result

    def load_and_render(self, prompt_name: str, variables: Dict[str, Any]) -> str:
        """Load template from file and render with variables."""
        template_str = self.load_prompt(prompt_name)
        return self.render_prompt(template_str, variables)
