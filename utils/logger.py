"""Application logging helpers."""

from __future__ import annotations

import logging

_LOGGER_CONFIGURED = False


def _configure_logging() -> None:
    global _LOGGER_CONFIGURED
    if _LOGGER_CONFIGURED:
        return

    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    if not root_logger.handlers:
        root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)

    _LOGGER_CONFIGURED = True


def get_logger(name: str = "dynamic_etl") -> logging.Logger:
    """Return a logger configured with the shared formatter/handlers."""

    _configure_logging()
    return logging.getLogger(name)
