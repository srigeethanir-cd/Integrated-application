from pathlib import Path
import hashlib
from jinja2 import Environment, FileSystemLoader, select_autoescape

class PromptBuilder:
    """Render the Jinja2 prompt for test generation.

    The template resides in ``backend/app/prompts/test_generation.jinja2``.
    ``build_prompt`` receives the Stage‑3 structured JSON and a list of
    categories that should be covered. It returns a deterministic prompt string
    suitable for the LLM.
    """

    def __init__(self, template_name: str = "test_generation.jinja2"):
        # Resolve the absolute path to the prompts directory relative to this file
        base_dir = Path(__file__).resolve().parents[2] / "prompts"
        self.env = Environment(
            loader=FileSystemLoader(base_dir),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self.template = self.env.get_template(template_name)

    def build_prompt(self, stage3_payload: dict, categories: list[str]) -> str:
        """Render the prompt.

        Args:
            stage3_payload: Structured Code Understanding JSON from Stage 3.
            categories: List of category names that the LLM must address.
        """
        payload = stage3_payload
        if not any(
            key in payload
            for key in ("generation_context", "regeneration_feedback")
        ):
            payload = {"generation_context": stage3_payload}
        return self.template.render(payload=payload, categories=categories)

    def cache_fingerprint(self) -> str:
        """Return a digest of the active generation prompt template.

        Returns:
            SHA-256 digest that changes whenever prompt source changes.
        """
        source, _, _ = self.env.loader.get_source(self.env, self.template.name)
        return hashlib.sha256(source.encode("utf-8")).hexdigest()
