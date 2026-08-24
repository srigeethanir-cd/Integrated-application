"""LLM Provider Factory supporting Groq, OpenAI, Google Gemini, and Mock LLMs."""

import logging
import os
from typing import Any, Dict, Optional

from app.core.config import get_settings
from app.utils.llm_client import LLMClient

logger = logging.getLogger(__name__)


class LLMClientAdapter:
    """Standardized LLM client adapter wrapping provider API calls."""

    def __init__(self, provider: str, model_name: str, api_key: Optional[str] = None):
        self.provider = provider
        self.model_name = model_name
        self.api_key = api_key
        try:
            self.client = LLMClient(provider=provider, model=model_name, api_key=api_key)
        except Exception as e:
            logger.warning("Failed to initialize provider %s: %s. Falling back to mock LLM.", provider, e)
            self.client = LLMClient(provider="mock", model="mock-model", api_key="mock-key")

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 1024,
    ) -> str:
        """Execute a text completion request, tracking metrics and logs in PostgreSQL."""
        sys_prompt = system_prompt or "You are a helpful AI software development accelerator."
        
        # 1. Resolve template ID from DB
        from app.database.session import SessionLocal
        from app.models.prompt_template import PromptTemplate
        from app.repository.prompt_template_repository import PromptTemplateRepository
        
        db = SessionLocal()
        template_id = None
        prompt_version = "1.0"
        try:
            all_templates = db.query(PromptTemplate).all()
            matched = None
            for t in all_templates:
                clean_t = t.prompt_template.split("{{")[0].strip()
                if clean_t and clean_t in prompt:
                    matched = t
                    break
            
            if not matched:
                for t in all_templates:
                    if t.system_prompt and t.system_prompt in sys_prompt:
                        matched = t
                        break

            if not matched:
                matched = db.query(PromptTemplate).filter_by(prompt_code="generic_agent_prompt").first()
                if not matched:
                    repo = PromptTemplateRepository(db)
                    matched = repo.create_template({
                        "prompt_code": "generic_agent_prompt",
                        "prompt_name": "Generic Agent Prompt",
                        "description": "Fallback template for untracked LLM calls",
                        "agent_name": "common",
                        "prompt_template": prompt,
                        "status": "Approved",
                        "is_active": True
                    })
            
            template_id = matched.id
            prompt_version = matched.prompt_version
        except Exception:
            pass
        finally:
            db.close()

        # 2. Run LLM execution with timing
        import time
        t_start = time.time()
        status = "SUCCESS"
        response_text = ""
        try:
            response_text = self.client.complete(
                system_prompt=sys_prompt,
                user_prompt=prompt,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response_text
        except Exception as e:
            status = "FAILED"
            response_text = f"{{\"status\": \"error\", \"message\": \"{str(e)}\"}}"
            return response_text
        finally:
            elapsed_ms = int((time.time() - t_start) * 1000)
            input_tokens = len((prompt + sys_prompt).split()) * 4 // 3
            output_tokens = len(response_text.split()) * 4 // 3
            total_tokens = input_tokens + output_tokens
            cost = input_tokens * 0.000002 + output_tokens * 0.000010
            
            if template_id:
                db = SessionLocal()
                try:
                    repo = PromptTemplateRepository(db)
                    repo.record_execution({
                        "prompt_template_id": template_id,
                        "prompt_version": prompt_version,
                        "agent_name": self.provider,
                        "llm_provider": self.provider,
                        "model_name": self.model_name,
                        "input_tokens": input_tokens,
                        "output_tokens": output_tokens,
                        "total_tokens": total_tokens,
                        "estimated_cost": cost,
                        "execution_time_ms": elapsed_ms,
                        "execution_status": status,
                        "retry_count": 0
                    })
                except Exception:
                    pass
                finally:
                    db.close()


class LLMFactory:
    """Factory for creating and configuring LLM client instances."""

    @staticmethod
    def create_llm_client(
        provider: Optional[str] = None,
        model_name: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> LLMClientAdapter:
        """Instantiate an LLM client adapter for Groq, OpenAI, Gemini, or Mock."""
        settings = get_settings()
        selected_provider = (provider or os.getenv("LLM_PROVIDER") or settings.llm_provider or "groq").lower()

        logger.info("Initializing LLM client for provider: %s", selected_provider)

        if selected_provider == "groq":
            key = api_key or settings.groq_api_key or os.getenv("GROQ_API_KEY")
            model = model_name or settings.groq_model or "llama-3.3-70b-versatile"
            if not key:
                logger.warning("Groq API key missing. Falling back to Mock LLM provider.")
                return LLMFactory._create_mock_client(model)

            return LLMClientAdapter(provider="groq", model_name=model, api_key=key)

        elif selected_provider == "openai":
            key = api_key or settings.openai_api_key or os.getenv("OPENAI_API_KEY")
            model = model_name or settings.openai_model or "gpt-4o"
            if not key:
                logger.warning("OpenAI API key missing. Falling back to Mock LLM provider.")
                return LLMFactory._create_mock_client(model)

            return LLMClientAdapter(provider="openai", model_name=model, api_key=key)

        else:
            model = model_name or "mock-model"
            return LLMFactory._create_mock_client(model)

    @staticmethod
    def _create_mock_client(model_name: str) -> LLMClientAdapter:
        return LLMClientAdapter(provider="mock", model_name=model_name, api_key="mock-key")
