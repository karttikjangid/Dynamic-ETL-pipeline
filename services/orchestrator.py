"""Service-level orchestrators."""

from __future__ import annotations

from typing import Tuple


def get_db_and_collection(source_id: str) -> Tuple[str, str]:
    """Return database and collection names for a source."""

    raise NotImplementedError


def handle_duplicate_upload(source_id: str, new_schema) -> bool:
    """Handle duplicate uploads without creating new schema versions."""

    raise NotImplementedError
