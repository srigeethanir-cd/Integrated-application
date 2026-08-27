"""
Groq API Client Service – Hybrid LLM Layer.

Manages connection to Groq API using key loaded from app/.env or OS environment.
Provides structured JSON generation and code completion with automatic model selection
and exception safety (falling back cleanly when LLM is unavailable or fails).
"""

import json
import logging
import os
import re
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Default Groq Models
PRIMARY_MODEL = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")
FALLBACK_MODEL = os.getenv("GROQ_FALLBACK_MODEL", "qwen/qwen3.6-27b")
GROQ_COMPLETIONS_URL = "https://api.groq.com/openai/v1/chat/completions"


def get_groq_api_key() -> Optional[str]:
    """Retrieve Groq API key from environment variables or .env file."""
    # 1. Check OS environment case-insensitively
    for k, v in os.environ.items():
        if k.lower() == "groq_api_key" and v and v.strip() and not v.startswith("your_groq"):
            return v.strip().strip('"').strip("'")

    # 2. Check various .env paths
    env_paths = [
        os.path.join(os.path.dirname(__file__), "..", "..", ".env"),
        os.path.join(os.path.dirname(__file__), "..", ".env"),
        os.path.join(os.getcwd(), ".env"),
        os.path.join(os.getcwd(), "app", ".env"),
        "/workspace/.env",
        "/workspace/app/.env",
    ]

    for ep in env_paths:
        if os.path.exists(ep):
            try:
                with open(ep, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("#") or not line:
                            continue
                        if "=" in line:
                            var_name, var_val = line.split("=", 1)
                            if var_name.strip().lower() == "groq_api_key":
                                k = var_val.strip().strip('"').strip("'")
                                if k and not k.startswith("your_groq"):
                                    return k
            except Exception as exc:
                logger.debug("Error reading %s: %s", ep, exc)

    return None


class GroqLLMClient:
    """Client wrapper for Groq LLM API with fallback safety."""

    def __init__(self, api_key: Optional[str] = None, timeout: int = 30):
        self.api_key = api_key or get_groq_api_key()
        self.timeout = timeout

    @property
    def is_available(self) -> bool:
        """Check if a valid Groq API key is present."""
        return bool(self.api_key and len(self.api_key) > 10)

    def generate_chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = PRIMARY_MODEL,
        temperature: float = 0.2,
        json_mode: bool = False,
    ) -> Optional[str]:
        """Execute chat completion request against Groq API using standard urllib."""
        if not self.is_available:
            logger.warning("GroqLLMClient: No GROQ_API_KEY found. Falling back to deterministic layer.")
            return None

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }

        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 4096,
        }

        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        req = urllib.request.Request(
            GROQ_COMPLETIONS_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                choices = result.get("choices", [])
                if choices:
                    return choices[0].get("message", {}).get("content", "")
        except urllib.error.HTTPError as exc:
            err_body = exc.read().decode("utf-8") if hasattr(exc, "read") else str(exc)
            logger.warning("Groq API HTTPError (%d) with model %s: %s", exc.code, model, err_body)
            # Try secondary model on rate limit or model failure
            if model != FALLBACK_MODEL:
                logger.info("Retrying Groq request with fallback model '%s'", FALLBACK_MODEL)
                return self.generate_chat_completion(messages, model=FALLBACK_MODEL, temperature=temperature, json_mode=json_mode)
        except Exception as exc:
            logger.warning("Groq API Request failed with model %s: %s", model, exc)
            if model != FALLBACK_MODEL:
                return self.generate_chat_completion(messages, model=FALLBACK_MODEL, temperature=temperature, json_mode=json_mode)

        return None

    def generate_json(self, prompt: str, system_prompt: str = "You are a senior QA engineer. Return strictly valid JSON.") -> Optional[Dict[str, Any]]:
        """Request structured JSON from Groq LLM."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]
        raw = self.generate_chat_completion(messages, json_mode=True)
        if not raw:
            return None

        # Clean markdown codeblocks if returned
        clean_raw = raw.strip()
        if clean_raw.startswith("```json"):
            clean_raw = clean_raw[7:]
        if clean_raw.startswith("```"):
            clean_raw = clean_raw[3:]
        if clean_raw.endswith("```"):
            clean_raw = clean_raw[:-3]
        clean_raw = clean_raw.strip()

        try:
            return json.loads(clean_raw)
        except json.JSONDecodeError as exc:
            logger.warning("Failed to parse LLM JSON response: %s\nRaw output: %s", exc, raw[:200])
            # Attempt regex JSON extraction
            match = re.search(r"(\{.*\}|\[.*\])", clean_raw, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except Exception:
                    pass
            return None

    def generate_code(self, prompt: str, system_prompt: str) -> Optional[str]:
        """Request clean source code output from Groq LLM."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]
        raw = self.generate_chat_completion(messages, json_mode=False)
        if not raw:
            return None

        clean_raw = raw.strip()
        # Strip markdown fences if present
        if "```" in clean_raw:
            match = re.search(r"```(?:tsx|jsx|ts|js|typescript|javascript)?\n(.*?)```", clean_raw, re.DOTALL)
            if match:
                return match.group(1).strip()
        return clean_raw
