"""Identifier and slug generation utilities."""

import re
import uuid


def generate_uuid() -> str:
    """Generate a standard UUID v4 string."""
    return str(uuid.uuid4())


def normalize_story_key(raw_key: str) -> str:
    """Normalize user story key into standardized format (e.g., US001)."""
    if not raw_key:
        return "US001"
    clean = re.sub(r"[^A-Za-z0-9]", "", str(raw_key)).upper()
    if not clean.startswith("US"):
        clean = f"US{clean}"
    return clean


def generate_slug(text: str) -> str:
    """Convert a natural-language title or string into a URL-friendly slug."""
    text = str(text).lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")
