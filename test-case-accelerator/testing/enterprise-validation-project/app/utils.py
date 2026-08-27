import re

EMAIL_PATTERN = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


def validate_email(email: str) -> bool:
    """Return exactly whether an email satisfies the supported syntax."""
    return bool(EMAIL_PATTERN.fullmatch(email.strip()))


def normalize_search_terms(terms: list[str]) -> list[str]:
    """Normalize, de-duplicate, and preserve first-seen ordering."""
    normalized: list[str] = []
    for term in terms:
        value = term.strip().lower()
        if value and value not in normalized:
            normalized.append(value)
    return normalized

