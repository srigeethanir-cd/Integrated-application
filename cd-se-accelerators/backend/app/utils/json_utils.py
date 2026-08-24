import json
import re
from typing import Any, Dict


def extract_json(text: str) -> Dict[str, Any]:
    """Extract and parse the first valid JSON object from an LLM response string.

    Handles three common LLM output patterns:
    1. Pure JSON response.
    2. JSON wrapped in a markdown code block (```json ... ```).
    3. JSON embedded inside prose text.

    Raises:
        ValueError: If no valid JSON object can be found in the text.
    """
    # Pattern 1: strip markdown fences
    fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence_match:
        candidate = fence_match.group(1)
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    # Pattern 2: find the outermost {...} block
    brace_match = re.search(r"\{.*\}", text, re.DOTALL)
    if brace_match:
        candidate = brace_match.group(0)
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    # Pattern 3: try the whole string directly
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    raise ValueError(
        f"No valid JSON object found in LLM response.\n"
        f"Response snippet: {text[:300]!r}"
    )


def safe_extract_json(text: str, fallback: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Like extract_json but returns fallback dict on failure instead of raising."""
    try:
        return extract_json(text)
    except ValueError:
        return fallback or {}
