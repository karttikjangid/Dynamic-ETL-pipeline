"""Normalization orchestration helpers."""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, List

from core import NormalizedRecord

from .json_normalizer import JSONNormalizer
from .kv_normalizer import KVNormalizer


def normalize_all_records(raw_records: List[Dict]) -> List[NormalizedRecord]:
    """Normalize heterogeneous records by source type.
    
    Takes extracted records, categorizes them by source_type,
    dispatches to appropriate normalizer, and returns combined results.
    
    Args:
        raw_records: List of ExtractedRecord dicts with keys:
            - data: Dict[str, Any]
            - source_type: str ("json" or "kv")
            - confidence: float
            
    Returns:
        List of NormalizedRecord objects
    """
    # Group records by source type
    categorized = categorize_records(raw_records)
    
    # Process each category through its normalizer
    normalized_results = []
    
    for source_type, records in categorized.items():
        normalized = normalize_by_type(records, source_type)
        normalized_results.extend(normalized)
    
    return normalized_results


def categorize_records(records: List[Dict]) -> Dict[str, List[Dict]]:
    """Group records by their source type.
    
    Args:
        records: List of ExtractedRecord dicts
        
    Returns:
        Dict mapping source_type -> list of records
        e.g., {"json": [...], "kv": [...]}
    """
    categorized = {}
    
    for record in records:
        source_type = record.get("source_type", "unknown")
        
        if source_type not in categorized:
            categorized[source_type] = []
        
        categorized[source_type].append(record)
    
    return categorized


def normalize_by_type(records: List[Dict], source_type: str) -> List[NormalizedRecord]:
    """Dispatch to the proper normalizer implementation.
    
    Routes records to JSONNormalizer or KVNormalizer based on source_type.
    
    Args:
        records: List of ExtractedRecord dicts of the same source_type
        source_type: "json" or "kv"
        
    Returns:
        List of NormalizedRecord objects
    """
    # Prepare records for normalizer (extract data + metadata)
    normalizer_input = [
        {
            "data": record["data"],
            "source_type": record["source_type"],
            "confidence": record.get("confidence", 1.0)
        }
        for record in records
    ]
    
    # Route to appropriate normalizer
    if source_type == "json":
        json_normalizer = JSONNormalizer()
        return json_normalizer.normalize(normalizer_input)
    elif source_type == "kv":
        kv_normalizer = KVNormalizer()
        return kv_normalizer.normalize(normalizer_input)
    else:
        # Unknown source type - return empty list
        return []


def normalize_fragment(fragment: Dict) -> Dict:
    """Normalize a single fragment with type and content fields.
    
    This is a convenience function for normalizing individual fragments
    in the format: {"type": "json|kv", "content": {...}}
    
    Args:
        fragment: Dict with keys:
            - type: str ("json" or "kv")
            - content: Dict[str, Any] (raw data to normalize)
            
    Returns:
        Dict with same structure but normalized content
    """
    frag_type = fragment.get("type", "unknown")
    content = fragment.get("content", {})
    
    # Prepare record for normalizer
    record = {
        "data": content,
        "source_type": frag_type,
        "confidence": 1.0
    }
    
    # Normalize using appropriate normalizer
    normalized_records = normalize_by_type([record], frag_type)
    
    # Extract normalized content
    if normalized_records:
        normalized_content = normalized_records[0].data
    else:
        # If normalization failed, return original content
        normalized_content = content
    
    # Return fragment with updated content
    return {
        "type": frag_type,
        "content": normalized_content
    }
