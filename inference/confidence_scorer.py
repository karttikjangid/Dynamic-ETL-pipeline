"""Confidence scoring helpers for schema inference."""

from __future__ import annotations

from typing import Dict, List


def compute_confidence(type_counts: Dict[str, int], total_observations: int) -> float:
    """Calculate confidence score based on type distribution.
    
    This is the core confidence calculation function. It measures how
    consistent a field's type is across all observations by calculating
    the ratio of the dominant type to total observations.
    
    Args:
        type_counts: Dictionary mapping type names to their occurrence counts
                    e.g., {"integer": 8, "string": 2}
        total_observations: Total number of observations (sum of all counts)
        
    Returns:
        Confidence score between 0.0 and 1.0, rounded to 3 decimal places
        
    Rules:
        - Confidence = dominant_type_count / total_observations
        - Rounded to 3 decimals for consistency
        - If total_observations = 0, returns 0.0 (no data)
        - Higher score = more consistent type usage
        - Low confidence (< 0.6) indicates mixed types
        
    Use Cases:
        - Schema inference: Determine if a field has a stable type
        - Data quality: Identify fields with inconsistent types
        - Migration planning: Flag fields needing type coercion
        
    Examples:
        >>> compute_confidence({"integer": 10}, 10)
        1.0
        >>> compute_confidence({"integer": 8, "string": 2}, 10)
        0.8
        >>> compute_confidence({"string": 5, "null": 5}, 10)
        0.5
        >>> compute_confidence({}, 0)
        0.0
        
    Rationale:
        A simple ratio provides an intuitive confidence metric:
        - 1.0 = perfect consistency (all same type)
        - 0.8+ = high confidence (mostly one type)
        - 0.6-0.8 = moderate confidence (some variation)
        - < 0.6 = low confidence (mixed types, needs attention)
    """
    # Handle edge case: no observations
    if total_observations == 0:
        return 0.0
    
    # Handle edge case: empty type_counts
    if not type_counts:
        return 0.0
    
    # Find the count of the most common type
    dominant_count = max(type_counts.values())
    
    # Calculate confidence ratio
    confidence = dominant_count / total_observations
    
    # Round to 3 decimals for consistency
    return round(confidence, 3)


def semantic_confidence_boost(
    semantics: Dict[str, bool], dominant_type: str
) -> float:
    """Calculate confidence boost based on semantic type hints.
    
    This function provides a small confidence boost when a field appears
    to have semantic meaning beyond its basic type. For example, a string
    field that consistently looks like a date has higher confidence than
    a plain string field.
    
    Args:
        semantics: Dictionary of semantic flags from detect_semantics()
                  {"looks_like_number": bool, "looks_like_date": bool, 
                   "looks_like_boolean": bool}
        dominant_type: The most common type detected (e.g., "string")
        
    Returns:
        Boost value to add to base confidence (0.0 to 0.05)
        
    Rules:
        - If dominant_type == "string" but looks_like_date=True → +0.05
        - If dominant_type == "string" but looks_like_number=True → +0.02
        - If dominant_type == "string" but looks_like_boolean=True → +0.02
        - Boost is small to avoid over-inflating confidence
        - Multiple boosts do NOT stack (maximum single boost applies)
        - Final confidence after boost never exceeds 1.0
        
    Use Cases:
        - Reward semantic consistency: "2024-01-15" is more structured than "hello"
        - Distinguish structured strings from free text
        - Identify fields suitable for type casting
        
    Examples:
        >>> semantic_confidence_boost({"looks_like_date": True}, "string")
        0.05
        >>> semantic_confidence_boost({"looks_like_number": True}, "string")
        0.02
        >>> semantic_confidence_boost({"looks_like_date": False}, "string")
        0.0
        >>> semantic_confidence_boost({"looks_like_date": True}, "integer")
        0.0
        
    Rationale:
        Semantic consistency is valuable for schema inference:
        - Date strings: Strongly structured, +0.05 boost
        - Numeric strings: Moderately structured, +0.02 boost
        - Boolean strings: Moderately structured, +0.02 boost
        - Plain strings: No boost (could be anything)
        
        The boost is intentionally small (max 5%) to avoid:
        - Masking real type inconsistencies
        - Over-confidence in inferred schemas
        - Treating semantic hints as strongly as actual types
    """
    # Only boost string types with semantic hints
    if dominant_type != "string":
        return 0.0
    
    # Check semantic flags (prioritize strongest signal)
    if semantics.get("looks_like_date", False):
        return 0.05  # Dates are highly structured
    
    if semantics.get("looks_like_number", False):
        return 0.02  # Numbers are moderately structured
    
    if semantics.get("looks_like_boolean", False):
        return 0.02  # Booleans are moderately structured
    
    # No semantic hints detected
    return 0.0


def calculate_field_confidence(
    records: List[Dict], field_name: str, detected_type: str
) -> float:
    """Aggregate multiple heuristics to produce a confidence score.
    
    This is the high-level function that combines multiple confidence
    signals to produce a final confidence score for a field.
    
    Args:
        records: List of record dictionaries (NormalizedRecord.data)
        field_name: Name of the field to analyze
        detected_type: The dominant type detected for this field
        
    Returns:
        Final confidence score between 0.0 and 1.0
        
    Process:
        1. Count field occurrences across records
        2. Check type consistency for this field
        3. Combine signals into final confidence score
        
    Examples:
        >>> records = [
        ...     {"age": 25, "name": "Alice"},
        ...     {"age": 30, "name": "Bob"},
        ...     {"age": 28}
        ... ]
        >>> calculate_field_confidence(records, "age", "integer")
        1.0
    """
    from .type_mapper import infer_type
    
    if not records:
        return 0.0
    
    # Count how many records have this field
    field_count = count_field_occurrences(records, field_name)
    
    if field_count == 0:
        return 0.0
    
    # Check type consistency
    type_consistency = check_type_consistency(records, field_name, detected_type)
    
    # For now, type consistency is our primary signal
    # Future: Could combine with other heuristics
    return type_consistency


def count_field_occurrences(records: List[Dict], field_name: str) -> int:
    """Count how many records contain the field.
    
    This helper function counts the presence of a field across records,
    which helps determine field coverage and optionality.
    
    Args:
        records: List of record dictionaries
        field_name: Name of the field to count
        
    Returns:
        Number of records containing this field
        
    Use Cases:
        - Determine if field is required or optional
        - Calculate field coverage percentage
        - Identify sparse fields
        
    Examples:
        >>> records = [
        ...     {"age": 25, "name": "Alice"},
        ...     {"age": 30},
        ...     {"name": "Bob"}
        ... ]
        >>> count_field_occurrences(records, "age")
        2
        >>> count_field_occurrences(records, "name")
        2
        >>> count_field_occurrences(records, "missing")
        0
    """
    count = 0
    
    for record in records:
        if field_name in record:
            count += 1
    
    return count


def check_type_consistency(
    records: List[Dict], field_name: str, expected_type: str
) -> float:
    """Measure how often a field matches the expected type.
    
    This function examines all occurrences of a field and calculates
    what percentage match the expected type.
    
    Args:
        records: List of record dictionaries
        field_name: Name of the field to check
        expected_type: The type we expect (e.g., "integer", "string")
        
    Returns:
        Consistency ratio between 0.0 and 1.0, rounded to 3 decimals
        
    Process:
        1. Find all records containing the field
        2. Check actual type of each occurrence
        3. Calculate ratio of matches to total occurrences
        
    Examples:
        >>> records = [
        ...     {"age": 25},
        ...     {"age": 30},
        ...     {"age": "unknown"}
        ... ]
        >>> check_type_consistency(records, "age", "integer")
        0.667
    """
    from .type_mapper import infer_type
    
    if not records:
        return 0.0
    
    # Collect all values for this field
    matching_count = 0
    total_count = 0
    
    for record in records:
        if field_name in record:
            value = record[field_name]
            actual_type = infer_type(value)
            
            total_count += 1
            if actual_type == expected_type:
                matching_count += 1
    
    # Calculate consistency ratio
    if total_count == 0:
        return 0.0
    
    consistency = matching_count / total_count
    return round(consistency, 3)
