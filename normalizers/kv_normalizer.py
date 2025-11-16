"""Key-value normalization utilities."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from core import NormalizedRecord

from .base import BaseNormalizer


class KVNormalizer(BaseNormalizer):
    """Normalize key-value pairs into canonical dictionaries."""

    def normalize(self, records: List[Dict]) -> List[NormalizedRecord]:
        """Normalize list of KV records into NormalizedRecord objects.
        
        Args:
            records: List of dicts with 'data', 'source_type', 'confidence' keys
            
        Returns:
            List of NormalizedRecord objects with normalized data
        """
        normalized = []
        
        for record in records:
            # Extract data and metadata
            raw_data = record.get("data", {})
            source_type = record.get("source_type", "kv")
            confidence = record.get("confidence", 1.0)
            
            # Normalize the KV data
            normalized_data = normalize_kv_record(raw_data)
            
            if normalized_data is not None:
                # Create NormalizedRecord
                norm_record = NormalizedRecord(
                    data=normalized_data,
                    source_type=source_type,
                    extraction_confidence=confidence,
                    provenance={"source": source_type}
                )
                normalized.append(norm_record)
        
        return normalized


def normalize_kv_record(record: Dict[str, str]) -> Optional[Dict]:
    """Normalize a single key-value record.
    
    Args:
        record: Dictionary with string keys and values
        
    Returns:
        Normalized dictionary with typed values, or None if empty
    """
    if not record:
        return None
    
    normalized = {}
    
    for key, value in record.items():
        # Standardize key name
        clean_key = _standardize_key(key)
        
        # Infer and convert value type
        typed_value = infer_value_type(value)
        
        normalized[clean_key] = typed_value
    
    return normalized


def infer_value_type(value: str) -> Any:
    """Infer primitive types from string values.
    
    Converts string values to appropriate Python types:
    - Booleans: "true"/"false" → True/False
    - Integers: "42" → 42
    - Floats: "3.14" → 3.14
    - Null-like: "null", "none", "-", "n/a" → None
    - ISO dates: kept as strings (YYYY-MM-DD or ISO 8601 format)
    - Everything else: kept as string
    
    Args:
        value: String value to type-infer
        
    Returns:
        Typed value (bool, int, float, None, or str)
    """
    # Handle non-string input (in case of nested structures)
    if not isinstance(value, str):
        # Recursively handle nested structures
        if isinstance(value, dict):
            return {k: infer_value_type(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [infer_value_type(item) for item in value]
        else:
            return value
    
    # Strip whitespace
    value = value.strip()
    
    # Empty string
    if not value:
        return ""
    
    # Null-like values (case-insensitive)
    value_lower = value.lower()
    if value_lower in ("null", "none", "nil", "-", "n/a", "na", "n.a.", "n.a"):
        return None
    
    # Boolean values (case-insensitive)
    if value_lower == "true":
        return True
    if value_lower == "false":
        return False
    
    # ISO date patterns - keep as strings (no parsing)
    # Pattern 1: YYYY-MM-DD
    if re.match(r'^\d{4}-\d{2}-\d{2}$', value):
        return value
    
    # Pattern 2: ISO 8601 datetime
    # YYYY-MM-DDTHH:MM:SS or with timezone/milliseconds
    if re.match(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', value):
        return value
    
    # Try integer conversion
    try:
        # Check if it's a clean integer (no decimal point)
        if '.' not in value and 'e' not in value_lower and 'E' not in value:
            int_val = int(value)
            return int_val
    except (ValueError, OverflowError):
        pass
    
    # Try float conversion
    try:
        float_val = float(value)
        return float_val
    except (ValueError, OverflowError):
        pass
    
    # Keep as string if no type matched
    return value


def standardize_key_names(record: Dict) -> Dict:
    """Convert keys into deterministic naming convention.
    
    This is the public API for key standardization.
    
    Args:
        record: Dictionary with potentially inconsistent key names
        
    Returns:
        Dictionary with standardized key names
    """
    return {_standardize_key(k): v for k, v in record.items()}


def _standardize_key(key: str) -> str:
    """Standardize a single key name.
    
    Rules:
    - Convert to lowercase
    - Replace spaces, hyphens with underscores
    - Remove special characters except underscores
    - Remove leading/trailing underscores
    - Collapse multiple underscores to single
    
    Args:
        key: Original key name
        
    Returns:
        Standardized key name
    """
    if not isinstance(key, str):
        key = str(key)
    
    # Convert to lowercase
    key = key.lower()
    
    # Replace spaces and hyphens with underscores
    key = key.replace(' ', '_').replace('-', '_')
    
    # Remove special characters except underscores and alphanumeric
    key = re.sub(r'[^a-z0-9_]', '', key)
    
    # Collapse multiple underscores
    key = re.sub(r'_+', '_', key)
    
    # Remove leading/trailing underscores
    key = key.strip('_')
    
    # Ensure key is not empty
    if not key:
        key = "unknown"
    
    return key
