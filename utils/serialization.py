"""Helpers for converting Python-native types into JSON-serializable data."""

from __future__ import annotations

from datetime import date, datetime, time
from typing import Any


def coerce_to_json_serializable(value: Any) -> Any:
    """Recursively convert values into JSON-serializable representations.

    Ensures objects like ``datetime`` and ``date`` are turned into ISO8601
    strings before they enter schema inference or storage layers.
    """

    if isinstance(value, dict):
        return {key: coerce_to_json_serializable(val) for key, val in value.items()}

    if isinstance(value, list):
        return [coerce_to_json_serializable(item) for item in value]

    if isinstance(value, tuple):
        return [coerce_to_json_serializable(item) for item in value]

    if isinstance(value, set):
        return [coerce_to_json_serializable(item) for item in sorted(value, key=str)]

    if isinstance(value, (datetime, date, time)):
        return value.isoformat()

    return value
