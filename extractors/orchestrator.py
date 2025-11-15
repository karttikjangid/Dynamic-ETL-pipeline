"""Extraction orchestration helpers."""

from __future__ import annotations

from typing import Dict, List, Tuple

from core import ExtractedRecord
from utils.logger import get_logger

from .file_parser import parse_file
from .json_extractor import JSONExtractor
from .kv_extractor import KVExtractor

logger = get_logger(__name__)


def extract_all_records(file_path: str) -> Tuple[List[ExtractedRecord], Dict[str, int]]:
    """Run all extractors against the file and return stats.
    
    Args:
        file_path: Path to the file to extract from
        
    Returns:
        Tuple of (all_records, extraction_stats)
    """
    # Parse the file to get text content
    text = parse_file(file_path)
    
    # Initialize extractors
    json_extractor = JSONExtractor()
    kv_extractor = KVExtractor()
    
    # Extract JSON fragments
    json_records = json_extractor.extract(text)
    
    # Extract KV fragments (already avoids JSON regions internally)
    kv_records = kv_extractor.extract(text)
    
    # Combine records
    all_records = combine_extracted_records(json_records, kv_records)
    
    # Build stats
    stats = {
        "json_fragments": len(json_records),
        "kv_pairs": len(kv_records),
        "total_records": len(all_records)
    }
    
    # Log stats
    log_extraction_stats(stats)
    
    return all_records, stats


def combine_extracted_records(
    json_records: List[ExtractedRecord],
    kv_records: List[ExtractedRecord],
) -> List[ExtractedRecord]:
    """Merge JSON and KV results preserving ordering metadata.
    
    Combines records from different extractors and sorts them by
    their position in the original text (if position metadata available).
    
    Args:
        json_records: Records from JSON extractor
        kv_records: Records from KV extractor
        
    Returns:
        Combined and sorted list of ExtractedRecord objects
    """
    # Combine all records
    all_records = json_records + kv_records
    
    # Note: Since ExtractedRecord doesn't have start/end fields,
    # we maintain the order: JSON first, then KV
    # This is deterministic and preserves extraction order
    
    return all_records


def log_extraction_stats(stats: Dict[str, int]) -> None:
    """Send extraction metrics to the shared logger.
    
    Args:
        stats: Dictionary containing extraction statistics
    """
    logger.info("Extraction complete:")
    logger.info(f"  JSON fragments: {stats.get('json_fragments', 0)}")
    logger.info(f"  KV pairs: {stats.get('kv_pairs', 0)}")
    logger.info(f"  Total records: {stats.get('total_records', 0)}")
