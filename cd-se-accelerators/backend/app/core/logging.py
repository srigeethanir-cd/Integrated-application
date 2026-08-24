"""Shared structured logging configuration for AI BA Accelerator."""

import json
import logging
import logging.config
import os
from pathlib import Path


def setup_logging(config_path: str = "configs/logging.json", default_level: str = "INFO") -> None:
    """Initialize structured logging based on JSON config file or fallback to basic config."""
    # Ensure logs directory exists
    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            logging.config.dictConfig(config)
            logging.getLogger(__name__).debug("Loaded logging configuration from %s", config_path)
            return
        except Exception as e:
            print(f"Warning: Failed to load logging config from {config_path}: {e}. Falling back to standard logging.")

    # Fallback configuration
    level = getattr(logging, default_level.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def get_logger(name: str) -> logging.Logger:
    """Retrieve a named logger instance."""
    logger = logging.getLogger(name)
    if not logger.handlers and not logging.getLogger().handlers:
        setup_logging()
    return logger
