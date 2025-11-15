"""Schema generation orchestration."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List
from uuid import uuid4

from core import SchemaField, SchemaMetadata

from .confidence_scorer import calculate_field_confidence
from .schema_detector import detect_data_types
from .genson_integration import generate_genson_schema, extract_fields_from_genson_schema, compute_schema_signature


def generate_schema(
    records: List[Dict], source_id: str, version: int = 1
) -> SchemaMetadata:
    """
    Produce a SchemaMetadata instance for the given records.
    
    This function analyzes a list of records and generates a comprehensive
    schema definition including field types, confidence scores, and metadata.
    
    Args:
        records: List of dictionaries representing normalized data records
        source_id: Identifier for the data source
        version: Schema version number (default: 1)
    
    Returns:
        SchemaMetadata object containing the complete schema definition
    
    Example:
        >>> records = [
        ...     {"id": 1, "name": "Alice", "active": True},
        ...     {"id": 2, "name": "Bob", "active": False}
        ... ]
        >>> schema = generate_schema(records, "users", version=1)
        >>> len(schema.fields)
        3
    """
    # Handle empty records
    if not records:
        return SchemaMetadata(
            schema_id=f"{source_id}_v{version}_{uuid4().hex[:8]}",
            source_id=source_id,
            version=version,
            fields=[],
            generated_at=datetime.now(),
            record_count=0,
            extraction_stats={"total_records": 0, "empty_records": 0}
        )
    
    # Detect field types across all records
    field_types = detect_data_types(records)
    
    # Generate Genson schema for Tier-B
    genson_schema = generate_genson_schema(records)
    
    # Calculate confidence for each field
    field_confidences = {}
    for field_name, field_type in field_types.items():
        field_confidences[field_name] = calculate_field_confidence(
            records, field_name, field_type
        )
    
    # Build schema fields
    schema_fields = build_schema_fields(records, field_types, field_confidences)
    
    # Generate schema ID
    schema_id = f"{source_id}_v{version}_{uuid4().hex[:8]}"
    
    # Collect extraction stats
    extraction_stats = {
        "total_records": len(records),
        "fields_detected": len(field_types),
        "avg_confidence": sum(field_confidences.values()) / len(field_confidences) if field_confidences else 0.0
    }
    
    return SchemaMetadata(
        schema_id=schema_id,
        source_id=source_id,
        version=version,
        fields=schema_fields,
        generated_at=datetime.now(),
        record_count=len(records),
        extraction_stats=extraction_stats,
        genson_schema=genson_schema  # Tier-B: Store Genson schema
    )


def build_schema_fields(
    records: List[Dict],
    field_types: Dict[str, str],
    field_confidences: Dict[str, float],
) -> List[SchemaField]:
    """
    Build SchemaField objects with examples and confidences.
    
    This function constructs SchemaField objects for each detected field,
    including type information, nullability, confidence scores, and 
    example values for documentation.
    
    Args:
        records: List of record dictionaries
        field_types: Mapping of field names to their detected types
        field_confidences: Mapping of field names to confidence scores
    
    Returns:
        List of SchemaField objects, one per detected field
    
    Example:
        >>> records = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
        >>> field_types = {"id": "integer", "name": "string"}
        >>> field_confidences = {"id": 1.0, "name": 1.0}
        >>> fields = build_schema_fields(records, field_types, field_confidences)
        >>> len(fields)
        2
    """
    schema_fields = []
    
    for field_name, field_type in field_types.items():
        # Check if field is nullable (appears in all records)
        present_count = sum(1 for record in records if field_name in record)
        is_nullable = present_count < len(records)
        
        # Extract example value (first non-None value found)
        example_value = None
        for record in records:
            if field_name in record and record[field_name] is not None:
                example_value = record[field_name]
                break
        
        # Get confidence score
        confidence = field_confidences.get(field_name, 0.5)
        
        # Create SchemaField
        schema_field = SchemaField(
            name=field_name,
            type=field_type,
            nullable=is_nullable,
            example_value=example_value,
            confidence=confidence
        )
        
        schema_fields.append(schema_field)
    
    return schema_fields


def extract_example_values(
    records: List[Dict], field_names: List[str]
) -> Dict[str, Any]:
    """
    Capture representative values for documentation.
    
    This function extracts example values for specified fields, which
    can be used for API documentation, schema visualization, or testing.
    
    Args:
        records: List of record dictionaries
        field_names: List of field names to extract examples for
    
    Returns:
        Dictionary mapping field names to example values
    
    Example:
        >>> records = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
        >>> examples = extract_example_values(records, ["id", "name"])
        >>> examples["name"]
        'Alice'
    """
    examples = {}
    
    for field_name in field_names:
        # Find first non-None value for this field
        for record in records:
            if field_name in record and record[field_name] is not None:
                examples[field_name] = record[field_name]
                break
        
        # If no value found, mark as None
        if field_name not in examples:
            examples[field_name] = None
    
    return examples


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
