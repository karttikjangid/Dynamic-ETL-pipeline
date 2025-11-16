"""Map low-level Arrow types to application-level types."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict, List, Tuple


def infer_type(value: Any) -> str:
    """Infer the JSON-schema-like type of a Python value.
    
    This function maps Python types to standardized type strings
    that align with JSON schema conventions. It is deterministic
    and handles all common Python types.
    
    Args:
        value: Any Python value to inspect
        
    Returns:
        One of: "null", "boolean", "integer", "number", "string",
                "object", "array", "unknown"
                
    Rules:
        - None → "null"
        - bool → "boolean" (checked before int due to bool subclass)
        - int → "integer"
        - float → "number"
        - str → "string" (no automatic conversion)
        - dict → "object"
        - list/tuple → "array"
        - everything else → "unknown"
        
    Examples:
        >>> infer_type(None)
        'null'
        >>> infer_type(True)
        'boolean'
        >>> infer_type(42)
        'integer'
        >>> infer_type(3.14)
        'number'
        >>> infer_type("hello")
        'string'
        >>> infer_type({"key": "value"})
        'object'
        >>> infer_type([1, 2, 3])
        'array'
    """
    # Handle None first
    if value is None:
        return "null"
    
    # Check bool BEFORE int (bool is subclass of int in Python)
    if isinstance(value, bool):
        return "boolean"
    
    # Check integer
    if isinstance(value, int):
        return "integer"
    
    # Check float/number
    if isinstance(value, float):
        return "number"
    
    # Check string (no auto-conversion)
    if isinstance(value, str):
        return "string"
    
    # Check dict/object
    if isinstance(value, dict):
        return "object"
    
    # Check list/tuple/array
    if isinstance(value, (list, tuple)):
        return "array"
    
    # Everything else is unknown
    return "unknown"


def is_numeric_string(s: str) -> bool:
    r"""Detect if string matches strict integer or float pattern.
    
    This function uses a strict regex pattern to identify numeric strings.
    It does NOT use float() parsing to avoid accepting fuzzy formats.
    
    Args:
        s: String to test
        
    Returns:
        True if string is a valid integer or float, False otherwise
        
    Accepts:
        - "42"
        - "-42"
        - "+42"
        - "3.14"
        - "-3.14"
        - "0.5"
        - ".5"
        
    Rejects:
        - "12,000" (comma separators)
        - "1.2.3" (multiple decimals)
        - "$20" (currency symbols)
        - "5%" (percentage signs)
        - "1e3" (scientific notation)
        - "1.2.3.4" (IP addresses)
        - "abc"
        - ""
        
    Pattern breakdown:
        ^           - Start of string
        [+-]?       - Optional sign
        \d*         - Zero or more digits before decimal
        \.?         - Optional decimal point
        \d+         - One or more digits (required somewhere)
        $           - End of string
        
    Examples:
        >>> is_numeric_string("42")
        True
        >>> is_numeric_string("3.14")
        True
        >>> is_numeric_string("12,000")
        False
        >>> is_numeric_string("1e3")
        False
    """
    if not isinstance(s, str) or not s:
        return False
    
    # Strict numeric pattern: optional sign, digits, optional decimal
    # Must have at least one digit
    pattern = r'^[+-]?\d*\.?\d+$'
    
    return bool(re.match(pattern, s))


def is_boolean_string(s: str) -> bool:
    """Check if string represents a boolean value.
    
    This function matches common boolean representations in a
    case-insensitive manner.
    
    Args:
        s: String to test
        
    Returns:
        True if string matches boolean pattern, False otherwise
        
    Accepts (case-insensitive):
        - "true" / "false"
        - "yes" / "no"
        
    Rejects:
        - "1" / "0" (ambiguous)
        - "on" / "off" (ambiguous)
        - "t" / "f" (too short)
        - Empty strings
        
    Examples:
        >>> is_boolean_string("true")
        True
        >>> is_boolean_string("FALSE")
        True
        >>> is_boolean_string("yes")
        True
        >>> is_boolean_string("NO")
        True
        >>> is_boolean_string("1")
        False
    """
    if not isinstance(s, str) or not s:
        return False
    
    # Case-insensitive check
    normalized = s.strip().lower()
    
    return normalized in {"true", "false", "yes", "no"}


def is_iso_date_string(s: str) -> bool:
    """Check if string is a valid ISO 8601 date/datetime.
    
    This function accepts ONLY strict ISO 8601 formats and does
    NOT perform fuzzy date parsing to avoid false positives.
    
    Args:
        s: String to test
        
    Returns:
        True if string is valid ISO 8601 format, False otherwise
        
    Accepts:
        - "2024-01-15" (YYYY-MM-DD)
        - "2024-01-15T08:30" (YYYY-MM-DDTHH:MM)
        - "2024-01-15T08:30:45" (YYYY-MM-DDTHH:MM:SS)
        - "2024-01-15T08:30:45.123" (with microseconds)
        
    Rejects:
        - "01/15/2024" (US format)
        - "15-01-2024" (EU format)
        - "2024/01/15" (slash separators)
        - "Jan 15, 2024" (textual)
        - "20240115" (no separators)
        - Invalid dates like "2024-02-30"
        
    Strategy:
        1. Use regex to check format structure
        2. Use datetime.fromisoformat() to validate actual date
        3. No fuzzy parsing libraries
        
    Examples:
        >>> is_iso_date_string("2024-01-15")
        True
        >>> is_iso_date_string("2024-01-15T08:30:45")
        True
        >>> is_iso_date_string("01/15/2024")
        False
        >>> is_iso_date_string("2024-02-30")
        False
    """
    if not isinstance(s, str) or not s:
        return False
    
    # Regex pattern for ISO 8601 formats
    # YYYY-MM-DD or YYYY-MM-DDTHH:MM or YYYY-MM-DDTHH:MM:SS[.ffffff]
    pattern = r'^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}(:\d{2}(\.\d+)?)?)?$'
    
    if not re.match(pattern, s):
        return False
    
    # Validate with datetime.fromisoformat()
    try:
        datetime.fromisoformat(s)
        return True
    except (ValueError, TypeError):
        return False


def detect_semantics(s: str) -> Dict[str, bool]:
    """Analyze string to detect semantic type hints.
    
    This function examines a string value and determines if it
    has semantic meaning beyond being a plain string (e.g., looks
    like a number, date, or boolean).
    
    Args:
        s: String to analyze
        
    Returns:
        Dictionary with semantic flags:
        {
            "looks_like_number": bool,
            "looks_like_date": bool,
            "looks_like_boolean": bool
        }
        
    Behavior:
        - Never raises exceptions
        - Returns all False for non-strings or None
        - Uses strict helper functions (no fuzzy matching)
        - Deterministic and consistent
        
    Examples:
        >>> detect_semantics("42")
        {'looks_like_number': True, 'looks_like_date': False, 'looks_like_boolean': False}
        >>> detect_semantics("2024-01-15")
        {'looks_like_number': False, 'looks_like_date': True, 'looks_like_boolean': False}
        >>> detect_semantics("true")
        {'looks_like_number': False, 'looks_like_date': False, 'looks_like_boolean': True}
        >>> detect_semantics("hello")
        {'looks_like_number': False, 'looks_like_date': False, 'looks_like_boolean': False}
    """
    # Initialize result with all False
    result = {
        "looks_like_number": False,
        "looks_like_date": False,
        "looks_like_boolean": False
    }
    
    # Handle non-string gracefully
    if not isinstance(s, str):
        return result
    
    # Check each semantic type using helper functions
    try:
        result["looks_like_number"] = is_numeric_string(s)
        result["looks_like_date"] = is_iso_date_string(s)
        result["looks_like_boolean"] = is_boolean_string(s)
    except Exception:
        # Defensive: if any check fails, return partial results
        pass
    
    return result


def merge_types(types: List[str]) -> Tuple[str, List[str]]:
    """Calculate dominant type and union from a list of types.
    
    This function analyzes a collection of type strings and determines
    the most common (dominant) type, along with a sorted union of all
    distinct types present.
    
    Args:
        types: List of type strings (e.g., ["integer", "string", "integer"])
        
    Returns:
        Tuple of (dominant_type, sorted_union_list)
        
    Rules:
        1. Dominant type = most frequent type
        2. If "integer" and "number" both present, treat as "number"
        3. For ties, use alphabetical order as tie-breaker
        4. Union list is sorted alphabetically
        5. Empty input returns ("unknown", [])
        
    Type Promotion:
        - If both "integer" and "number" exist:
          - Combine counts
          - Dominant becomes "number"
          - Union contains only "number" (not both)
          
    Examples:
        >>> merge_types(["integer", "integer", "string"])
        ('integer', ['integer', 'string'])
        
        >>> merge_types(["integer", "number", "integer"])
        ('number', ['number'])
        
        >>> merge_types(["string", "null", "string"])
        ('string', ['null', 'string'])
        
        >>> merge_types([])
        ('unknown', [])
        
        >>> merge_types(["boolean", "boolean", "string", "string"])
        ('boolean', ['boolean', 'string'])  # alphabetical tie-break
    """
    if not types:
        return ("unknown", [])
    
    # Count frequency of each type
    type_counts = {}
    for t in types:
        type_counts[t] = type_counts.get(t, 0) + 1
    
    # Handle integer + number promotion
    if "integer" in type_counts and "number" in type_counts:
        # Combine counts into "number"
        combined_count = type_counts["integer"] + type_counts["number"]
        del type_counts["integer"]
        type_counts["number"] = combined_count
    
    # Find dominant type (most frequent)
    # If tie, use alphabetical order
    if type_counts:
        # Sort by count (descending), then by name (ascending)
        sorted_types = sorted(
            type_counts.items(),
            key=lambda x: (-x[1], x[0])  # negative count for descending, name for ascending
        )
        dominant_type = sorted_types[0][0]
    else:
        dominant_type = "unknown"
    
    # Create sorted union list
    union_list = sorted(type_counts.keys())
    
    return (dominant_type, union_list)

