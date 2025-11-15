"""Schema generation orchestration."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from core import SchemaField, SchemaMetadata

from .confidence_scorer import calculate_field_confidence
from .schema_detector import detect_data_types


def generate_schema(
    records: List[Dict], source_id: str, version: int = 1
) -> SchemaMetadata:
    """Produce a SchemaMetadata instance for the given records."""

    raise NotImplementedError


def build_schema_fields(
    records: List[Dict],
    field_types: Dict[str, str],
    field_confidences: Dict[str, float],
) -> List[SchemaField]:
    """Build SchemaField objects with examples and confidences."""

    raise NotImplementedError


def extract_example_values(
    records: List[Dict], field_names: List[str]
) -> Dict[str, Any]:
    """Capture representative values for documentation."""

    raise NotImplementedError


def compute_schema_diff(
    old_schema: SchemaMetadata, new_schema: SchemaMetadata
) -> Dict[str, Any]:
    """
    Compare two schema versions and return a structured diff.

    This function identifies added, removed, and changed fields between
    two schema versions. It's useful for:
    - Schema evolution tracking
    - Migration planning
    - Breaking change detection
    - Schema version comparison

    Args:
        old_schema: The previous schema version
        new_schema: The current schema version

    Returns:
        A dictionary with three keys:
        - "added": List of field names that exist only in new_schema
        - "removed": List of field names that exist only in old_schema
        - "changed": Dict mapping field names to their old/new field details
                    Only includes fields where:
                    - type changed
                    - nullable status changed

    Example:
        >>> old = SchemaMetadata(
        ...     schema_id="schema_v1",
        ...     source_id="orders",
        ...     version=1,
        ...     generated_at=datetime.now(),
        ...     record_count=10,
        ...     extraction_stats={},
        ...     fields=[
        ...         SchemaField(name="id", type="integer"),
        ...         SchemaField(name="status", type="string"),
        ...     ]
        ... )
        >>> new = SchemaMetadata(
        ...     schema_id="schema_v2",
        ...     source_id="orders",
        ...     version=2,
        ...     generated_at=datetime.now(),
        ...     record_count=10,
        ...     extraction_stats={},
        ...     fields=[
        ...         SchemaField(name="id", type="string"),
        ...         SchemaField(name="created_at", type="string"),
        ...     ]
        ... )
        >>> diff = compute_schema_diff(old, new)
        >>> diff["added"]
        ['created_at']
        >>> diff["removed"]
        ['status']
        >>> "id" in diff["changed"]
        True
    """
    # Build field name indices for both schemas
    old_fields_by_name = {field.name: field for field in old_schema.fields}
    new_fields_by_name = {field.name: field for field in new_schema.fields}

    # Extract field name sets
    old_names = set(old_fields_by_name.keys())
    new_names = set(new_fields_by_name.keys())

    # Compute set differences
    added_names = sorted(new_names - old_names)
    removed_names = sorted(old_names - new_names)

    # Detect semantic changes in fields that exist in both schemas
    changed = {}
    common_names = old_names & new_names

    for name in sorted(common_names):
        old_field = old_fields_by_name[name]
        new_field = new_fields_by_name[name]

        # Track all semantic differences
        differences = {}

        # Check type change
        if old_field.type != new_field.type:
            differences["type"] = {
                "old": old_field.type,
                "new": new_field.type,
            }

        # Check nullable change
        if old_field.nullable != new_field.nullable:
            differences["nullable"] = {
                "old": old_field.nullable,
                "new": new_field.nullable,
            }

        # Check confidence change (significant if > 0.1 difference)
        conf_diff = abs(old_field.confidence - new_field.confidence)
        if conf_diff > 0.1:
            differences["confidence"] = {
                "old": old_field.confidence,
                "new": new_field.confidence,
            }

        # If any differences found, record the change
        if differences:
            changed[name] = {
                "old": {
                    "type": old_field.type,
                    "nullable": old_field.nullable,
                    "confidence": old_field.confidence,
                },
                "new": {
                    "type": new_field.type,
                    "nullable": new_field.nullable,
                    "confidence": new_field.confidence,
                },
                "differences": differences,
            }

    return {
        "added": added_names,
        "removed": removed_names,
        "changed": changed,
    }
