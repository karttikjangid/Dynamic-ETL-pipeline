"""Extraction orchestration helpers."""

from __future__ import annotations

from typing import Dict, List, Tuple

from core import ExtractedRecord

from .json_extractor import JSONExtractor
from .kv_extractor import KVExtractor


def extract_all_records(file_path: str) -> Tuple[List[ExtractedRecord], Dict[str, int]]:
    """Run all extractors against the file and return stats."""

    raise NotImplementedError


def combine_extracted_records(
    json_records: List[ExtractedRecord],
    kv_records: List[ExtractedRecord],
) -> List[ExtractedRecord]:
    """Merge JSON and KV results preserving ordering metadata."""

    raise NotImplementedError


def log_extraction_stats(stats: Dict[str, int]) -> None:
    """Send extraction metrics to the shared logger."""

    raise NotImplementedError
