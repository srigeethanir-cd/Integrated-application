import logging
from logging.config import dictConfig
from typing import Any

from app.core.constants import DEFAULT_LOG_LEVEL


def configure_logging() -> None:
    configuration: dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "level": DEFAULT_LOG_LEVEL,
            }
        },
        "root": {
            "handlers": ["console"],
            "level": DEFAULT_LOG_LEVEL,
        },
    }
    dictConfig(configuration)
    logging.captureWarnings(True)
