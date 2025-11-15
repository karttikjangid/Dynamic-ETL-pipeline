"""Application logging helpers."""

from __future__ import annotations

import logging
from typing import Optional

_LOGGER: Optional[logging.Logger] = None


def get_logger(name: str = "dynamic_etl") -> logging.Logger:
    """Return a module-level logger configured once."""

    global _LOGGER
    if _LOGGER is None:
        _LOGGER = logging.getLogger(name)
        if not _LOGGER.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            _LOGGER.addHandler(handler)
        _LOGGER.setLevel(logging.INFO)
    return _LOGGER
