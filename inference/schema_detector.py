"""Schema detection utilities."""

from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List, Optional

import pandas as pd


def walk_paths(obj: Any, parent_path: str = "") -> List[tuple]:
    """Recursively walk object structure and yield (path, value) pairs.
    
    This utility function traverses nested dictionaries and lists to
    extract all field paths and their values in a flattened format.
    
    Args:
        obj: The object to walk (dict, list, or scalar)
        parent_path: The accumulated path string (e.g., "user.address.city")
        
    Yields:
        Tuples of (path, value) for each scalar value found
        
    Examples:
        >>> list(walk_paths({"a": 1, "b": {"c": 2}}))
        [('a', 1), ('b.c', 2)]
        
        >>> list(walk_paths({"items": [{"id": 1}, {"id": 2}]}))
        [('items[].id', 1), ('items[].id', 2)]
    """
    paths = []
    
    if isinstance(obj, dict):
        for key, value in obj.items():
            new_path = f"{parent_path}.{key}" if parent_path else key
            
            if isinstance(value, (dict, list)):
                # Recursively walk nested structures
                paths.extend(walk_paths(value, new_path))
            else:
                # Scalar value
                paths.append((new_path, value))
    
    elif isinstance(obj, list):
        # For arrays, use [] notation and walk each item
        array_path = f"{parent_path}[]" if parent_path else "[]"
        for item in obj:
            if isinstance(item, (dict, list)):
                paths.extend(walk_paths(item, parent_path))
            else:
                paths.append((array_path, item))
    else:
        # Scalar at root (unusual but handle it)
        paths.append((parent_path or "value", obj))
    
    return paths


def collect_path_stats(parsed_fragments: List[Dict]) -> Dict[str, Dict]:
    """Collect comprehensive statistics for each field path in the data.
    
    This function analyzes all records to gather detailed statistics about
    each field path, including type distribution, examples, numeric stats,
    semantic hints, and uniqueness samples.
    
    Args:
        parsed_fragments: List of dictionaries representing normalized records
                         Each dict should contain the record data
                         
    Returns:
        Dictionary mapping field paths to their statistics:
        {
            "field.path": {
                "presence_count": int,
                "type_counts": Counter,
                "example_values": List[Any],  # up to 3 examples
                "numeric_stats": {
                    "min": float,
                    "max": float,
                    "count": int
                },
                "semantic_flags": {
                    "looks_like_number": int,  # count
                    "looks_like_date": int,
                    "looks_like_boolean": int
                },
                "sample_for_pk": List[Any]  # up to 500 scalar values
            }
        }
        
    Memory Safety:
        - Example values capped at 3
        - PK samples capped at 500
        - Deterministic ordering
        
    Use Cases:
        - Schema inference: Understand field characteristics
        - Data quality: Identify patterns and anomalies
        - PK detection: Gather uniqueness samples
        - Type coercion: Analyze type distributions
        
    Examples:
        >>> records = [
        ...     {"user_id": 1, "name": "Alice"},
        ...     {"user_id": 2, "name": "Bob"},
        ... ]
        >>> stats = collect_path_stats(records)
        >>> stats["user_id"]["presence_count"]
        2
    """
    from .type_mapper import infer_type, detect_semantics
    
    # Dictionary to accumulate statistics
    path_stats = {}
    
    # Process each record
    for record in parsed_fragments:
        # Walk all paths in this record
        paths = walk_paths(record)
        
        for path, value in paths:
            # Initialize stats for this path if first encounter
            if path not in path_stats:
                path_stats[path] = {
                    "presence_count": 0,
                    "type_counts": Counter(),
                    "example_values": [],
                    "numeric_stats": {
                        "min": None,
                        "max": None,
                        "count": 0
                    },
                    "semantic_flags": {
                        "looks_like_number": 0,
                        "looks_like_date": 0,
                        "looks_like_boolean": 0
                    },
                    "sample_for_pk": []
                }
            
            stats = path_stats[path]
            
            # Increment presence count
            stats["presence_count"] += 1
            
            # Track type
            value_type = infer_type(value)
            stats["type_counts"][value_type] += 1
            
            # Collect example values (cap at 3)
            if len(stats["example_values"]) < 3:
                # Avoid duplicate examples
                if value not in stats["example_values"]:
                    stats["example_values"].append(value)
            
            # Numeric statistics (for actual numbers)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                try:
                    if stats["numeric_stats"]["min"] is None:
                        stats["numeric_stats"]["min"] = value
                        stats["numeric_stats"]["max"] = value
                    else:
                        stats["numeric_stats"]["min"] = min(stats["numeric_stats"]["min"], value)
                        stats["numeric_stats"]["max"] = max(stats["numeric_stats"]["max"], value)
                    stats["numeric_stats"]["count"] += 1
                except (TypeError, ValueError):
                    # Skip if comparison fails
                    pass
            
            # Semantic analysis (for strings)
            if isinstance(value, str):
                try:
                    semantics = detect_semantics(value)
                    if semantics.get("looks_like_number"):
                        stats["semantic_flags"]["looks_like_number"] += 1
                    if semantics.get("looks_like_date"):
                        stats["semantic_flags"]["looks_like_date"] += 1
                    if semantics.get("looks_like_boolean"):
                        stats["semantic_flags"]["looks_like_boolean"] += 1
                except Exception:
                    # Skip on error
                    pass
            
            # Sample for PK detection (cap at 500, scalar values only)
            if len(stats["sample_for_pk"]) < 500:
                # Only sample scalar values (not dicts or lists)
                if not isinstance(value, (dict, list)):
                    stats["sample_for_pk"].append(value)
    
    return path_stats


def detect_pk_candidate(stats: Dict, presence_ratio: float) -> bool:
    """Detect if a field is a primary key candidate.
    
    A field is considered a potential primary key if it appears frequently,
    has mostly unique values, and uses a scalar type.
    
    Args:
        stats: Statistics dictionary for a single field (from collect_path_stats)
        presence_ratio: Ratio of presence (presence_count / total_records)
        
    Returns:
        True if field appears to be a primary key candidate, False otherwise
        
    Rules:
        1. presence_ratio >= 0.9 (appears in at least 90% of records)
        2. sampled uniqueness ratio >= 0.9 (at least 90% unique values)
        3. dominant type is scalar (not object or array)
        
    Rationale:
        Primary keys should be:
        - Present in nearly all records (required field)
        - Highly unique (minimal duplication)
        - Simple scalar types (integer, string, etc.)
        
    Use Cases:
        - Index optimization: Suggest indexes on PK candidates
        - Relationship detection: Identify foreign key relationships
        - Data quality: Flag potential PK violations
        
    Examples:
        >>> stats = {
        ...     "type_counts": Counter({"integer": 100}),
        ...     "sample_for_pk": list(range(100))
        ... }
        >>> detect_pk_candidate(stats, 1.0)
        True
        
        >>> stats = {
        ...     "type_counts": Counter({"string": 100}),
        ...     "sample_for_pk": ["A"] * 100  # Not unique
        ... }
        >>> detect_pk_candidate(stats, 1.0)
        False
    """
    # Rule 1: Check presence ratio
    if presence_ratio < 0.9:
        return False
    
    # Rule 3: Check if dominant type is scalar
    type_counts = stats.get("type_counts", Counter())
    if not type_counts:
        return False
    
    dominant_type = type_counts.most_common(1)[0][0]
    
    # Non-scalar types are not PK candidates
    if dominant_type in ("object", "array", "unknown"):
        return False
    
    # Rule 2: Check uniqueness ratio
    sample = stats.get("sample_for_pk", [])
    
    if not sample:
        return False
    
    # Calculate uniqueness
    unique_count = len(set(sample))
    total_count = len(sample)
    
    if total_count == 0:
        return False
    
    uniqueness_ratio = unique_count / total_count
    
    # Require 90% uniqueness
    return uniqueness_ratio >= 0.9


def detect_enum_suggestion(stats: Dict, presence_ratio: float) -> Optional[List]:
    """Suggest if a field should be an enumeration type.
    
    Fields with a small set of distinct values that appear frequently
    are good candidates for enum types, which provide better type safety
    and documentation than plain strings.
    
    Args:
        stats: Statistics dictionary for a single field
        presence_ratio: Ratio of presence (presence_count / total_records)
        
    Returns:
        Sorted list of enum options if field is enum candidate, None otherwise
        
    Rules:
        1. Distinct value count <= 10 (small set)
        2. presence_ratio >= 0.5 (appears in at least half of records)
        3. Return sorted list for determinism
        
    Rationale:
        Enum types are valuable when:
        - Limited set of valid values (easy to validate)
        - Commonly present (not sparse)
        - Predictable options (better documentation)
        
    Use Cases:
        - API schema generation: Define enum types
        - Data validation: Restrict to known values
        - Database constraints: Create CHECK constraints
        - UI generation: Populate dropdown menus
        
    Examples:
        >>> stats = {"sample_for_pk": ["active", "inactive", "pending"]}
        >>> detect_enum_suggestion(stats, 0.8)
        ['active', 'inactive', 'pending']
        
        >>> stats = {"sample_for_pk": list(range(100))}
        >>> detect_enum_suggestion(stats, 1.0)
        None
    """
    # Rule 2: Check presence ratio
    if presence_ratio < 0.5:
        return None
    
    # Get unique values from sample
    sample = stats.get("sample_for_pk", [])
    
    if not sample:
        return None
    
    # Calculate distinct values
    unique_values = set(sample)
    
    # Rule 1: Check if distinct count is small enough
    if len(unique_values) > 10:
        return None
    
    # Return sorted list for determinism
    # Convert to strings for sorting (handle mixed types)
    try:
        # Try to sort naturally if all same type
        sorted_values = sorted(unique_values)
    except TypeError:
        # Mixed types, sort by string representation
        sorted_values = sorted(unique_values, key=str)
    
    return sorted_values


def detect_coercion_suggestion(stats: Dict) -> Optional[str]:
    """Suggest type coercion opportunities for data quality improvement.
    
    Identifies cases where string fields contain values that could be
    parsed into more specific types, enabling better type safety and
    numeric operations.
    
    Args:
        stats: Statistics dictionary for a single field
        
    Returns:
        Suggestion string if coercion detected, None otherwise
        Currently returns: "strings_mostly_numeric" or None
        
    Rules:
        - If >= 60% of string occurrences look numeric
          → return "strings_mostly_numeric"
        - Else None
        
    Rationale:
        Type coercion is valuable when:
        - Most values match a specific pattern
        - Converting improves data usability
        - Schema migration is being planned
        
    Use Cases:
        - Data cleaning: Convert string numbers to numeric types
        - Migration planning: Identify fields needing ALTER COLUMN
        - Validation: Flag records that don't match pattern
        - Performance: Enable numeric indexes and operations
        
    Examples:
        >>> stats = {
        ...     "type_counts": Counter({"string": 10}),
        ...     "semantic_flags": {"looks_like_number": 8}
        ... }
        >>> detect_coercion_suggestion(stats)
        'strings_mostly_numeric'
        
        >>> stats = {
        ...     "type_counts": Counter({"string": 10}),
        ...     "semantic_flags": {"looks_like_number": 2}
        ... }
        >>> detect_coercion_suggestion(stats)
        None
    """
    # Get type counts
    type_counts = stats.get("type_counts", Counter())
    
    # Only suggest coercion if field is predominantly strings
    string_count = type_counts.get("string", 0)
    
    if string_count == 0:
        return None
    
    # Check how many strings look numeric
    semantic_flags = stats.get("semantic_flags", {})
    numeric_string_count = semantic_flags.get("looks_like_number", 0)
    
    # Calculate ratio
    numeric_ratio = numeric_string_count / string_count
    
    # Rule: If >= 60% of strings look numeric, suggest coercion
    if numeric_ratio >= 0.6:
        return "strings_mostly_numeric"
    
    return None


def detect_data_types(records: List[Dict]) -> Dict[str, str]:
    """Infer data types from normalized records.
    
    This is the high-level function that analyzes records and returns
    a simple mapping of field names to their detected types.
    
    Args:
        records: List of normalized record dictionaries
        
    Returns:
        Dictionary mapping field names to type strings
        
    Examples:
        >>> records = [{"age": 25}, {"age": 30}]
        >>> detect_data_types(records)
        {'age': 'integer'}
    """
    from .type_mapper import infer_type, merge_types
    
    if not records:
        return {}
    
    # Collect types for each field
    field_types = {}
    
    for record in records:
        for field_name, value in record.items():
            if field_name not in field_types:
                field_types[field_name] = []
            
            value_type = infer_type(value)
            field_types[field_name].append(value_type)
    
    # Merge types to get dominant type for each field
    result = {}
    for field_name, types in field_types.items():
        dominant_type, _ = merge_types(types)
        result[field_name] = dominant_type
    
    return result


def load_records_to_dataframe(records: List[Dict]) -> pd.DataFrame:
    """Load records into a pandas DataFrame for analysis.
    
    Converts a list of dictionaries into a pandas DataFrame, which
    provides convenient tools for statistical analysis and type inference.
    
    Args:
        records: List of record dictionaries
        
    Returns:
        pandas DataFrame containing the records
        
    Note:
        This function uses pandas, which is a heavy dependency.
        For production use, consider whether DataFrame is needed
        or if the stdlib-based functions above suffice.
        
    Examples:
        >>> records = [{"a": 1}, {"a": 2}]
        >>> df = load_records_to_dataframe(records)
        >>> len(df)
        2
    """
    if not records:
        return pd.DataFrame()
    
    return pd.DataFrame(records)
