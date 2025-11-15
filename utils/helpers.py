"""Miscellaneous helper functions."""

from __future__ import annotations

from typing import Any, Dict


def merge_dicts(base: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
    """Return a new dict merging base with overrides."""

    raise NotImplementedError


def chunk_list(items: list[Any], chunk_size: int):
    """Yield successive chunks from a list."""

    raise NotImplementedError
