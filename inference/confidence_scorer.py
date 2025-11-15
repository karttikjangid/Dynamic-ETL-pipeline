"""Confidence scoring helpers for schema inference."""

from __future__ import annotations

from typing import Dict, List


def calculate_field_confidence(
    records: List[Dict], field_name: str, detected_type: str
) -> float:
    """Aggregate multiple heuristics to produce a confidence score."""

    raise NotImplementedError


def count_field_occurrences(records: List[Dict], field_name: str) -> int:
    """Count how many records contain the field."""

    raise NotImplementedError


def check_type_consistency(
    records: List[Dict], field_name: str, expected_type: str
) -> float:
    """Measure how often a field matches the expected type."""

    raise NotImplementedError
