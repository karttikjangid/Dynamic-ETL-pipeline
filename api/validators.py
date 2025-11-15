"""Input validators for API payloads."""

from __future__ import annotations

from typing import Any, Dict


def validate_upload_payload(payload: Dict[str, Any]) -> None:
    """Validate upload payload structure."""

    raise NotImplementedError


def validate_query_payload(payload: Dict[str, Any]) -> None:
    """Validate strict query payloads."""

    raise NotImplementedError
