"""Map low-level Arrow types to application-level types."""

from __future__ import annotations

from typing import Dict


def map_pyarrow_to_app_type(type_str: str) -> str:
    """Return application-specific type names."""

    raise NotImplementedError


def get_type_mapping() -> Dict[str, str]:
    """Provide the canonical mapping dictionary."""

    raise NotImplementedError
