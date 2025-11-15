"""Shared validation helpers."""

from __future__ import annotations

from typing import Any, Dict


def ensure_required_keys(payload: Dict[str, Any], required_keys: set[str]) -> None:
    """Ensure payload contains all required keys."""

    raise NotImplementedError


def assert_supported_source_type(source_type: str, allowed: set[str]) -> None:
    """Validate that the source type is supported."""

    raise NotImplementedError
