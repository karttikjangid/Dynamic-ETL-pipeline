"""Normalization orchestration helpers."""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, List

from core import NormalizedRecord

from .json_normalizer import JSONNormalizer
from .kv_normalizer import KVNormalizer


def normalize_all_records(raw_records: List[Dict]) -> List[NormalizedRecord]:
    """Normalize heterogeneous records by source type."""

    raise NotImplementedError


def categorize_records(records: List[Dict]) -> Dict[str, List[Dict]]:
    """Group records by their source type."""

    raise NotImplementedError


def normalize_by_type(records: List[Dict], source_type: str) -> List[NormalizedRecord]:
    """Dispatch to the proper normalizer implementation."""

    raise NotImplementedError
