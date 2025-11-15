"""JSON record normalization."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Union

from core import NormalizedRecord

from .base import BaseNormalizer


class JSONNormalizer(BaseNormalizer):
    """Normalize JSON extractor output."""

    def normalize(self, records: List[Dict]) -> List[NormalizedRecord]:
        """Normalize list of JSON records into NormalizedRecord objects.
        
        Args:
            records: List of dicts with 'data', 'source_type', 'confidence' keys
            
        Returns:
            List of NormalizedRecord objects with normalized data
        """
        normalized = []
        
        for record in records:
            # Extract data and metadata
            raw_data = record.get("data", {})
            source_type = record.get("source_type", "json")
            confidence = record.get("confidence", 1.0)
            
            # Normalize the JSON data
            normalized_data = normalize_json_record(raw_data)
            
            if normalized_data is not None:
                # Create NormalizedRecord
                norm_record = NormalizedRecord(
                    data=normalized_data,
                    original_source=source_type,
                    extraction_confidence=confidence
                )
                normalized.append(norm_record)
        
        return normalized


def normalize_json_record(record: Dict) -> Optional[Dict]:
    """Normalize a single JSON record.
    
    Recursively processes the JSON structure, applying type inference
    to string values while preserving the overall shape.
    
    Args:
        record: Dictionary representing parsed JSON
        
    Returns:
        Normalized dictionary, or None if invalid
    """
    if not record:
        return None
    
    if not validate_json_record(record):
        return None
    
    # Clean and normalize all values recursively
    return clean_json_values(record)


def validate_json_record(record: Dict) -> bool:
    """Ensure record meets normalization rules.
    
    Args:
        record: Dictionary to validate
        
    Returns:
        True if record is valid for normalization
    """
    # Must be a dict
    if not isinstance(record, dict):
        return False
    
    # Must not be empty
    if not record:
        return False
    
    # All keys must be strings (JSON requirement)
    if not all(isinstance(k, str) for k in record.keys()):
        return False
    
    return True


def clean_json_values(value: Any) -> Any:
    """Recursively normalize JSON values.
    
    Applies type inference to string values while preserving
    the original JSON structure (dicts, lists, nested objects).
    
    Args:
        value: Any JSON value (dict, list, string, number, bool, None)
        
    Returns:
        Normalized value with same structure
    """
    # Handle None
    if value is None:
        return None
    
    # Handle dictionaries - recurse on all values
    if isinstance(value, dict):
        return {k: clean_json_values(v) for k, v in value.items()}
    
    # Handle lists - recurse on all elements
    if isinstance(value, list):
        return [clean_json_values(item) for item in value]
    
    # Handle strings - apply type inference
    if isinstance(value, str):
        return _infer_string_type(value)
    
    # Handle booleans - keep as-is (already typed in JSON)
    if isinstance(value, bool):
        return value
    
    # Handle numbers - keep as-is (already typed in JSON)
    if isinstance(value, (int, float)):
        return value
    
    # Fallback: return as-is for any other type
    return value


def _infer_string_type(value: str) -> Union[str, int, float, bool, None]:
    """Infer type from string value.
    
    Similar to KV normalizer's type inference, but tailored for JSON strings.
    
    Args:
        value: String value to type-infer
        
    Returns:
        Typed value (bool, int, float, None, or str)
    """
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
