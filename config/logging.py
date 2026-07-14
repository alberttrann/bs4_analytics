"""
config/logging.py
Logging configuration - colored console in dev, structured in prod.
Call configure_logging() at application startup.
"""

from __future__ import annotations

import logging
import logging.config
import os


def configure_logging(level: str | None = None) -> None:
    """
    Apply logging configuration.
    Level defaults to LOG_LEVEL env var, then 'INFO'.
    """
    effective_level = level or os.getenv("LOG_LEVEL", "INFO")

    config: dict = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "console": {
                "format": "%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
                "datefmt": "%H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "console",
                "stream": "ext://sys.stdout",
            },
        },
        "root": {
            "handlers": ["console"],
            "level": effective_level,
        },
        "loggers": {
            # Quiet noisy third-party loggers
            "uvicorn.access": {"level": "WARNING", "propagate": False},
            "httpx":          {"level": "WARNING", "propagate": False},
            "matplotlib":     {"level": "WARNING", "propagate": False},
        },
    }

    logging.config.dictConfig(config)
