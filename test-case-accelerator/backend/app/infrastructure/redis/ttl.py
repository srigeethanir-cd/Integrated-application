"""Central cache time-to-live values, expressed in seconds."""

from enum import IntEnum


class CacheTTL(IntEnum):
    """Default expiration periods for pipeline artifact caches."""

    DEPENDENCY_CACHE = 60 * 60
    CODE_UNDERSTANDING_CACHE = 6 * 60 * 60
    TEST_GENERATION_CACHE = 6 * 60 * 60
    VERIFICATION_CACHE = 6 * 60 * 60
    QUALITY_CACHE = 12 * 60 * 60
    RUNTIME_CACHE = 60 * 60
