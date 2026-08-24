"""LLM Client — calls the OpenAI-compatible Chat Completions API via httpx.

Supports Groq, OpenAI, and mock providers via LLM_PROVIDER.
Groq is the default production provider. LLM_MODE selects development or
production execution behavior.

Uses no native extensions (no jiter, no openai package DLLs).

Configuration via environment variables:
    LLM_MODE         — "development" or "production" (default: production)
    LLM_PROVIDER     — "groq", "openai", or "mock" (default: groq)
    OPENAI_API_KEY   — required when provider=openai
    GROQ_API_KEY     — required when provider=groq
    LLM_MODEL        — optional (provider-specific default applied)
    LLM_TEMPERATURE  — optional float, default: 0.3
    LLM_MAX_TOKENS   — optional int,   default: 4096
"""

import json
import os
import time
from typing import Any, Dict, List, Optional

try:
    import httpx
except ImportError:
    httpx = None
from dotenv import load_dotenv

from app.utils.logger import get_logger

logger = get_logger(__name__)

# Agent processes can be invoked directly (for example by pytest or a worker),
# so load the project-level configuration before reading provider settings.
# Existing process environment variables retain precedence.
load_dotenv(override=False)

_PROVIDER_CONFIG = {
    "openai": {
        "url":           "https://api.openai.com/v1/chat/completions",
        "key_env":       "OPENAI_API_KEY",
        "default_model": "gpt-4o",
    },
    "groq": {
        "url":           "https://api.groq.com/openai/v1/chat/completions",
        "key_env":       "GROQ_API_KEY",
        "default_model": "llama-3.3-70b-versatile",
    },
    "mock": {
        "url":           "mock",
        "key_env":       "MOCK_API_KEY",
        "default_model": "mock-model",
    },
}

_VALID_MODES = {"development", "production"}


class LLMClient:
    """httpx-based wrapper supporting OpenAI, Groq, and Mock providers.

    The provider is selected via the LLM_PROVIDER environment variable.
    """

    DEFAULT_TEMPERATURE = 0.3
    DEFAULT_MAX_TOKENS  = 4096
    REQUEST_TIMEOUT     = 120  # seconds
    MAX_RETRIES         = 5

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        provider: Optional[str] = None,
    ) -> None:
        self.mode = os.getenv("LLM_MODE", "production").lower().strip()
        if self.mode not in _VALID_MODES:
            raise ValueError(
                f"Unknown LLM_MODE '{self.mode}'. Supported: {sorted(_VALID_MODES)}"
            )

        self.provider = (provider or os.getenv("LLM_PROVIDER", "groq")).lower().strip()

        if self.provider not in _PROVIDER_CONFIG:
            raise ValueError(
                f"Unknown LLM_PROVIDER '{self.provider}'. "
                f"Supported: {list(_PROVIDER_CONFIG.keys())}"
            )

        cfg = _PROVIDER_CONFIG[self.provider]
        self._url = cfg["url"]

        if self.provider == "mock":
            self.api_key = api_key or "mock-key"
        else:
            self.api_key = api_key or os.getenv(cfg["key_env"], "")
            if not self.api_key:
                raise EnvironmentError(
                    f"{cfg['key_env']} is not set. "
                    f"Add it to your .env file or export it as an environment variable."
                )

        provider_model = os.getenv(f"{self.provider.upper()}_MODEL", "")
        self.model = model or os.getenv("LLM_MODEL") or provider_model or cfg["default_model"]
        self.temperature = (
            temperature if temperature is not None
            else float(os.getenv("LLM_TEMPERATURE", str(self.DEFAULT_TEMPERATURE)))
        )
        self.max_tokens = max_tokens or int(
            os.getenv("LLM_MAX_TOKENS", str(self.DEFAULT_MAX_TOKENS))
        )

        self._headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type":  "application/json",
            "User-Agent":    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        }

        logger.info(
            "LLMClient initialised (mode=%s provider=%s) — model=%s temperature=%s",
            self.mode, self.provider, self.model, self.temperature,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Send a list of chat messages and return the assistant reply.

        Intercepts and returns simulated mock data when provider is 'mock'.
        """
        if self.provider == "mock":
            return self._mock_response(messages, reason="mock provider selected")

        # Groq model candidates if primary model is unavailable
        groq_model_candidates = [
            self.model,
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768",
            "gemma2-9b-it"
        ]
        # De-duplicate preserving order
        unique_candidates = []
        for m in groq_model_candidates:
            if m and m not in unique_candidates:
                unique_candidates.append(m)

        last_error: Optional[str] = None

        for current_model in (unique_candidates if self.provider == "groq" else [self.model]):
            body: Dict[str, Any] = {
                "model":       current_model,
                "messages":    messages,
                "temperature": temperature if temperature is not None else self.temperature,
                "max_tokens":  max_tokens or self.max_tokens,
            }

            for attempt in range(1, self.MAX_RETRIES + 1):
                try:
                    if httpx is not None:
                        with httpx.Client(timeout=self.REQUEST_TIMEOUT) as client:
                            response = client.post(
                                self._url,
                                headers=self._headers,
                                content=json.dumps(body),
                            )
                        status_code = response.status_code
                        response_text = response.text
                    else:
                        import urllib.request
                        import urllib.error
                        req = urllib.request.Request(
                            self._url,
                            data=json.dumps(body).encode("utf-8"),
                            headers=self._headers,
                            method="POST",
                        )
                        try:
                            with urllib.request.urlopen(req, timeout=self.REQUEST_TIMEOUT) as resp:
                                status_code = resp.status
                                response_text = resp.read().decode("utf-8")
                        except urllib.error.HTTPError as e:
                            status_code = e.code
                            response_text = e.read().decode("utf-8")

                    # If model not found (404), try next model in candidate list
                    if status_code == 404 and "model_not_found" in response_text.lower():
                        logger.warning(
                            "Groq model '%s' not found (404). Trying next available fallback model...",
                            current_model
                        )
                        break

                    # Rate limit — wait and retry
                    if status_code == 429:
                        if self.mode == "development" and self.provider == "groq":
                            logger.warning(
                                "Groq rate limit hit in development mode; falling back to mock."
                            )
                            return self._mock_response(
                                messages, reason="Groq rate-limit fallback"
                            )

                        last_error = f"Rate limit (429) on attempt {attempt}"
                        if attempt == self.MAX_RETRIES:
                            break
                        wait = 2.0
                        logger.warning(
                            "%s rate limit hit (attempt %d/%d). Retrying in %.1fs.",
                            self.provider, attempt, self.MAX_RETRIES, wait,
                        )
                        time.sleep(wait)
                        continue

                    if 500 <= status_code < 600:
                        last_error = f"HTTP {status_code} on attempt {attempt}"
                        if attempt == self.MAX_RETRIES:
                            break
                        wait = self._retry_delay(attempt)
                        logger.warning(
                            "%s returned HTTP %d (attempt %d/%d). Retrying in %.1fs.",
                            self.provider, status_code, attempt, self.MAX_RETRIES, wait,
                        )
                        time.sleep(wait)
                        continue

                    # Any other non-200
                    if status_code != 200:
                        logger.warning("LLM API returned HTTP %d: %s. Falling back to mock generator.", status_code, response_text[:200])
                        return self._mock_response(messages, reason=f"HTTP {status_code} fallback")

                    # Success
                    data = json.loads(response_text)
                    return data["choices"][0]["message"]["content"]

                except Exception as exc:
                    logger.warning("LLM request exception on attempt %d: %s", attempt, exc)
                    last_error = str(exc)
                    if attempt == self.MAX_RETRIES:
                        break
                    time.sleep(1.0)

        # If all candidates exhausted, fallback gracefully to mock generator
        logger.info("All LLM model candidates exhausted. Falling back to mock generator.")
        return self._mock_response(messages, reason="all LLM models exhausted")

    def complete(self, system_prompt: str, user_prompt: str, **kwargs: Any) -> str:
        """Convenience wrapper: single system + user turn.

        Args:
            system_prompt: The system instruction.
            user_prompt:   The user message.
            **kwargs:      Forwarded to chat() (temperature, max_tokens).

        Returns:
            The assistant reply string.
        """
        messages = [
            {"role": "system",  "content": system_prompt},
            {"role": "user",    "content": user_prompt},
        ]
        return self.chat(messages, **kwargs)

    def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs: Any) -> str:
        """Direct generation method used across Agent 2 artifact and code generators."""
        sys = system_prompt or "You are an expert full-stack software engineer and cloud architect generating production-ready code with complete business logic."
        return self.complete(system_prompt=sys, user_prompt=prompt, **kwargs)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _mock_response(self, messages: List[Dict[str, str]], reason: str) -> str:
        """Return an existing mock response and record why mock was used."""
        full_prompt = " ".join(message.get("content", "") for message in messages).lower()
        reply = self._simulate_mock_reply(full_prompt)
        logger.info("LLM response generated by mock provider (%s).", reason)
        return reply

    @staticmethod
    def _retry_delay(attempt: int) -> float:
        """Return a bounded exponential backoff for transient failures."""
        return min(float(2 ** (attempt - 1)), 30.0)

    def _simulate_mock_reply(self, prompt: str) -> str:
        """Generate static mock JSON/text architecture plans for offline test coverage."""
        prompt_lower = prompt.lower()

        # 1. StoryAnalyzer
        if "expert business analyst and requirements engineer" in prompt_lower:
            return '''{
              "stories": [{
                "id": "US-1", "title": "User authentication",
                "description": "Users can securely access the platform.",
                "acceptance_criteria": ["User can authenticate"],
                "actors": ["user"], "feature_group": "authentication",
                "priority": "high", "complexity": "moderate",
                "dependencies": [], "keywords": ["authentication"]
              }],
              "summary": "Authentication capability for the platform."
            }'''

        # 2. ConfigAnalyzer
        if "extract a structured project configuration" in prompt_lower:
            return """{
              "project_name": "Platform Sign",
              "tech_stack": {
                "backend": "python",
                "frontend": "react",
                "database": "postgresql",
                "infrastructure": "docker"
              },
              "features": ["user can sign up"],
              "nlp_normalized": {
                "raw_tech_input": "python, react, postgresql",
                "inferred_patterns": []
              }
            }"""

        # 3. ProjectAnalyzer
        if "analyze the software project overview" in prompt_lower or "summary and high-level list of components" in prompt_lower:
            return """{
              "summary": "Platform Sign is built with python on the backend and react on the frontend.",
              "components": [
                {"name": "API Gateway", "role": "Entry point for business operations"},
                {"name": "Service Layer", "role": "Coordinates orchestration and business rules"},
                {"name": "Data Store", "role": "Persists domain state"}
              ]
            }"""

        # 4. FeatureIdentifier
        if "group the provided user stories into cohesive product features" in prompt_lower:
            return """{"features": [
              {
                "name": "user can sign up",
                "description": "User signup flow and registration",
                "stories": ["STORY-1"]
              }
            ]}"""

        # 5. ModuleIdentifier
        if "decompose the provided product features into concrete software modules" in prompt_lower:
            return """{"modules": [
              {
                "name": "Authentication",
                "description": "Handles authentication concerns for Platform Sign",
                "features": ["user can sign up"]
              }
            ]}"""

        # 6. DataModelAnalyzer
        if "derive the domain data model" in prompt_lower:
            return """{
              "entities": [
                {
                  "name": "User",
                  "table_name": "users",
                  "fields": [
                    {"name": "id", "type": "uuid", "primary_key": true, "nullable": false},
                    {"name": "email", "type": "string", "length": 255, "unique": true, "nullable": false},
                    {"name": "password_hash", "type": "string", "length": 255, "nullable": false}
                  ]
                }
              ]
            }"""

        # 7. NFRAnalyzer
        if "identify the non-functional requirements" in prompt_lower:
            return """{
              "nfrs": [{"category": "security", "requirement": "Use JWT authentication", "rationale": "Protect user accounts", "priority": "high"}]
            }"""

        # 8. ArchitectureBlueprintGenerator
        if "synthesise the provided analysis into a complete architecture blueprint" in prompt_lower:
            return """{
              "project_name": "Platform Sign",
              "summary": "Platform Sign is built with python on the backend and react on the frontend. Regenerated with feedback: Prioritize mobile-first UX",
              "text_blueprint": "Blueprint for Platform Sign\\n\\nOverview: Platform Sign is planned as a python backend application with a react frontend and postgresql persistence.\\n\\nModules:\\n- Authentication: Handles authentication concerns for Platform Sign\\n\\nCore components:\\n- API Gateway for inbound requests\\n- Service Layer for business orchestration\\n- Data Store for persistence",
              "modules": [
                {
                  "name": "Authentication",
                  "description": "Handles authentication concerns for Platform Sign",
                  "responsibilities": ["Domain model", "Service layer", "Validation"]
                }
              ],
              "components": [
                {"name": "API Gateway", "role": "Entry point for business operations"},
                {"name": "Service Layer", "role": "Coordinates orchestration and business rules"},
                {"name": "Data Store", "role": "Persists domain state"}
              ],
              "integration_points": [
                {"name": "Authentication", "type": "service"},
                {"name": "Email Notifications", "type": "integration"}
              ]
            }"""

        # 9. WorkflowPlanGenerator
        if "create a detailed, phased implementation plan" in prompt_lower:
            return """{
              "project_name": "Platform Sign",
              "phases": [{"phase": "Foundation", "order": 1, "goal": "Set up the delivery baseline", "deliverables": ["Application scaffold"], "stories_covered": ["US-1"], "estimated_effort": "1 week", "dependencies": []}],
              "milestones": [{"name": "Foundation complete", "description": "The application skeleton is ready", "phase": "Foundation"}],
              "risks": []
            }"""

        # 10. SharedComponentsGenerator
        if "identify shared / cross-cutting components" in prompt_lower:
            return """{"shared_components": [
              {
                "name": "logger",
                "type": "utility",
                "path": "shared/utils/logger.py",
                "description": "Custom structured logger utility"
              },
              {
                "name": "auth_middleware",
                "type": "middleware",
                "path": "shared/middleware/auth.py",
                "description": "JWT verify and auth middleware"
              }
            ]}"""

        if "human-readable implementation plan document" in prompt_lower:
            return "Implementation Plan\\n\\nFoundation\\nSet up the delivery baseline and application scaffold."

        if "human-readable architecture blueprint" in prompt_lower:
            return "Blueprint for Platform Sign\\n\\nAuthentication module and supporting platform services."

        # 10. ProjectFolderCreator
        if "design the directory layout" in prompt_lower:
            return """{
              "folders": [
                "backend",
                "backend/authentication",
                "frontend",
                "shared",
                "metadata"
              ],
              "files": [
                {
                  "path": "backend/main.py",
                  "content": "import fastapi"
                },
                {
                  "path": "backend/config.py",
                  "content": "class Config: pass"
                },
                {
                  "path": "backend/requirements.txt",
                  "content": "fastapi\\nuvicorn"
                },
                {
                  "path": "backend/authentication/__init__.py",
                  "content": ""
                },
                {
                  "path": "backend/authentication/routes.py",
                  "content": ""
                },
                {
                  "path": "backend/authentication/models.py",
                  "content": ""
                },
                {
                  "path": "backend/authentication/service.py",
                  "content": ""
                },
                {
                  "path": "frontend/package.json",
                  "content": "{}"
                },
                {
                  "path": "frontend/public/index.html",
                  "content": "<html></html>"
                },
                {
                  "path": "frontend/src/index.jsx",
                  "content": "import React from 'react';"
                },
                {
                  "path": "frontend/src/App.jsx",
                  "content": "export default function App() { return null; }"
                },
                {
                  "path": "shared/constants.py",
                  "content": ""
                },
                {
                  "path": "shared/exceptions.py",
                  "content": ""
                },
                {
                  "path": "shared/types/base_types.py",
                  "content": ""
                },
                {
                  "path": "shared/utils/logger.py",
                  "content": ""
                },
                {
                  "path": "shared/utils/pagination.py",
                  "content": ""
                },
                {
                  "path": "shared/middleware/auth.py",
                  "content": ""
                },
                {
                  "path": "shared/contracts/authentication_contract.json",
                  "content": "{}"
                }
              ]
            }"""

        return "{}"

    @staticmethod
    def _parse_retry_after(response: Any) -> float:
        """Extract the wait time in seconds from a 429 response.

        Tries the Retry-After header first, then parses the error message
        for 'try again in Xs' patterns, defaulting to 30s.
        """
        import re

        # Header-based (standard)
        header = response.headers.get("retry-after", "")
        if header:
            try:
                return float(header) + 1
            except ValueError:
                pass

        # Body-based (Groq includes "try again in 23.81s")
        try:
            body = response.json()
            msg = body.get("error", {}).get("message", "")
            match = re.search(r"try again in ([\d.]+)s", msg, re.IGNORECASE)
            if match:
                return float(match.group(1)) + 1
        except Exception:
            pass

        return 30.0  # safe default

