"""JSON record normalization."""

from __future__ import annotations

from typing import Dict, List, Optional

from core import NormalizedRecord

from .base import BaseNormalizer


class JSONNormalizer(BaseNormalizer):
    """Normalize JSON extractor output."""

    def normalize(self, records: List[Dict]) -> List[NormalizedRecord]:
        raise NotImplementedError


def normalize_json_record(record: Dict) -> Optional[Dict]:
    """Normalize a single JSON record."""

    raise NotImplementedError


def validate_json_record(record: Dict) -> bool:
    """Ensure record meets normalization rules."""

    raise NotImplementedError


def clean_json_values(record: Dict) -> Dict:
    """Standardize JSON values (dates, numbers, etc)."""

    raise NotImplementedError
