"""Key-value normalization utilities."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from core import NormalizedRecord

from .base import BaseNormalizer


class KVNormalizer(BaseNormalizer):
    """Normalize key-value pairs into canonical dictionaries."""

    def normalize(self, records: List[Dict]) -> List[NormalizedRecord]:
        raise NotImplementedError


def normalize_kv_record(record: Dict[str, str]) -> Optional[Dict]:
    """Normalize a single key-value record."""

    raise NotImplementedError


def infer_value_type(value: str) -> Any:
    """Infer primitive types from string values."""

    raise NotImplementedError


def standardize_key_names(record: Dict) -> Dict:
    """Convert keys into deterministic naming convention."""

    raise NotImplementedError
