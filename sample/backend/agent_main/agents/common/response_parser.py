"""Resilient LLM response parser for JSON, markdown blocks, and Pydantic models."""

import json
import logging
import re
from typing import Any, Dict, Optional, Type, TypeVar

from pydantic import BaseModel

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)


class ResponseParser:
    """Utility for cleaning and parsing raw LLM outputs into structured objects."""

    @staticmethod
    def strip_markdown(text: str) -> str:
        """Strip markdown code fence wrappers from raw LLM output."""
        if not text:
            return ""
        text = text.strip()
        # Remove ```json ... ``` or ``` ... ```
        pattern = r"^```(?:json)?\s*\n?(.*?)\n?```$"
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return text

    @staticmethod
    def extract_json(text: str) -> Dict[str, Any]:
        """Extract and parse the first valid JSON dictionary object in the text."""
        cleaned = ResponseParser.strip_markdown(text)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

        # Search for first { ... } block
        json_match = re.search(r"(\{.*\})", cleaned, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError as e:
                logger.warning("Failed to parse JSON substring: %s", e)

        return {"raw_output": text}

    @staticmethod
    def parse_pydantic(text: str, model_cls: Type[T]) -> Optional[T]:
        """Parse raw LLM output into a validated Pydantic model instance."""
        data = ResponseParser.extract_json(text)
        try:
            return model_cls.model_validate(data)
        except Exception as e:
            logger.error("Pydantic validation error for model %s: %s", model_cls.__name__, e)
            return None
