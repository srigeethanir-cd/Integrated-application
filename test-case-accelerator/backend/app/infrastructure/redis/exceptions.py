"""Redis infrastructure exceptions."""


class RedisInfrastructureError(RuntimeError):
    """Base exception for Redis infrastructure failures."""


class RedisConfigurationError(RedisInfrastructureError):
    """Raised when Redis configuration is missing or invalid."""


class RedisConnectionError(RedisInfrastructureError):
    """Raised when a Redis connection cannot be established."""


class RedisSerializationError(RedisInfrastructureError):
    """Raised when a cache value cannot be serialized or deserialized."""
