# Schema Generation & Versioning

This document details the dual-schema architecture, type inference mechanisms, and intelligent versioning system used in the ETL pipeline.

## Dual-Schema Architecture

The pipeline employs a **dual-schema architecture** for optimal performance and intelligent versioning:

### Primary Schema System (Custom Inference)

**Purpose**: Fast, ETL-optimized schema generation for pipeline operations

**Core Components**:
```python
# Type detection from records
field_types = detect_data_types(records)  # Maps field → type
schema_fields = build_schema_fields(records, field_types, field_confidences)
```

**Features**:
- **Simple type system**: `string`, `integer`, `number`, `boolean`, `object`, `array`, `null`
- **Rich metadata**: Confidence scores, nullability detection, example values
- **Performance**: Lightweight inference using `infer_type()` + `merge_types()`
- **Control**: Custom logic handles ETL-specific edge cases

**Output**: `SchemaField[]` with confidence scores, examples, and metadata

### Secondary Schema System (Genson)

**Purpose**: Advanced schema comparison for intelligent versioning

**Core Components**:
```python
# JSON Schema generation for versioning
genson_schema = generate_genson_schema(records)  # JSON Schema format
signature = compute_schema_signature(genson_schema)  # Hash for comparison
```

**Features**:
- **Standard JSON Schema**: Full JSON Schema specification compliance
- **Structural signatures**: Deterministic hashing for duplicate detection
- **Deep comparison**: Enables sophisticated schema evolution tracking
- **Interoperability**: Standard format for external tools

**Output**: Standard JSON Schema format for comparison operations

## Type Inference System

### Data Type Detection

The system infers types from actual data patterns:

```python
def infer_type(value: Any) -> str:
    """Infer JSON Schema type from Python value."""
    if value is None:
        return "null"
    elif isinstance(value, bool):
        return "boolean"
    elif isinstance(value, int):
        return "integer"
    elif isinstance(value, float):
        return "number"
    elif isinstance(value, str):
        # Additional string pattern detection
        if _is_date_string(value):
            return "string"  # Keep as string, add metadata
        return "string"
    elif isinstance(value, (list, tuple)):
        return "array"
    elif isinstance(value, dict):
        return "object"
    else:
        return "string"  # Fallback
```

### Type Merging Logic

When multiple records have different types for the same field:

```python
def merge_types(existing_type: str, new_type: str) -> str:
    """Merge conflicting types into most general type."""
    type_hierarchy = {
        "null": 0,
        "boolean": 1,
        "integer": 2,
        "number": 3,  # integer promotes to number
        "string": 4,  # catch-all type
        "array": 5,
        "object": 6
    }

    # Choose the more general type
    existing_rank = type_hierarchy.get(existing_type, 4)
    new_rank = type_hierarchy.get(new_type, 4)

    if existing_rank >= new_rank:
        return existing_type
    else:
        return new_type
```

### Confidence Scoring

Each field gets a confidence score based on:
- **Type consistency**: How many records agree on the type
- **Value patterns**: Regularity in data format
- **Completeness**: Percentage of non-null values

```python
def calculate_field_confidence(records: List[Dict], field_name: str) -> float:
    """Calculate confidence score for a field."""
    values = [record.get(field_name) for record in records]
    non_null_values = [v for v in values if v is not None]

    if not non_null_values:
        return 0.0

    # Type consistency
    types = [infer_type(v) for v in non_null_values]
    most_common_type = max(set(types), key=types.count)
    type_consistency = types.count(most_common_type) / len(types)

    # Completeness
    completeness = len(non_null_values) / len(values)

    # Combined confidence
    return (type_consistency * 0.7) + (completeness * 0.3)
```

## Versioning Logic

### Schema Signatures

**Version increments only on structural changes:**

1. **Signature Generation**: Create deterministic hash of schema structure
2. **Comparison**: Compare new vs existing schema signatures
3. **Decision**: Reuse version if identical, increment if different

### Duplicate Detection

```python
def handle_duplicate_upload(
    source_id: str,
    new_schema: SchemaMetadata,
    existing_schema: Optional[SchemaMetadata] = None,
) -> bool:
    """Determine if upload represents same schema as latest version."""

    if existing_schema is None:
        # Fetch from database
        existing_schema = schema_store.retrieve_schema(db, source_id)

    if existing_schema is None:
        return False

    # Use Genson signature if available (Tier-B), fallback to field signature (Tier-A)
    if new_schema.genson_schema and existing_schema.genson_schema:
        old_signature = compute_schema_signature(existing_schema.genson_schema)
        new_signature = compute_schema_signature(new_schema.genson_schema)
    else:
        old_signature = _schema_signature(existing_schema)
        new_signature = _schema_signature(new_schema)

    return old_signature == new_signature
```

### Field-Based Signature (Tier-A Fallback)

```python
def _schema_signature(schema: SchemaMetadata) -> Tuple[Tuple[str, str, bool], ...]:
    """Create signature from field name, type, and nullability."""
    return tuple(
        sorted((field.name, field.type, field.nullable) for field in schema.fields)
    )
```

### Genson-Based Signature (Tier-B)

```python
def compute_schema_signature(genson_schema: Dict[str, Any]) -> str:
    """Create deterministic signature from JSON Schema."""
    # Normalize and hash the schema structure
    normalized = json.dumps(genson_schema, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(normalized.encode()).hexdigest()
```

## Schema Evolution Tracking

### DeepDiff Integration

For advanced schema comparison:

```python
def compare_schemas_with_deepdiff(
    old_schema: Dict[str, Any],
    new_schema: Dict[str, Any]
) -> Dict[str, Any]:
    """Compare schemas using DeepDiff for detailed changes."""
    return DeepDiff(old_schema, new_schema, ignore_order=True)
```

### Schema Diff Conversion

```python
def convert_deepdiff_to_schema_diff(
    deepdiff_result: Dict[str, Any],
    old_fields: List[SchemaField],
    new_fields: List[SchemaField]
) -> SchemaDiff:
    """Convert DeepDiff results to SchemaDiff format."""

    added_fields = []
    removed_fields = []
    type_changes = {}

    # Extract changes from DeepDiff result
    for change_type, changes in deepdiff_result.items():
        if change_type == "dictionary_item_added":
            # New fields added
            for path in changes:
                field_name = _extract_field_name(path)
                added_fields.append(field_name)

        elif change_type == "dictionary_item_removed":
            # Fields removed
            for path in changes:
                field_name = _extract_field_name(path)
                removed_fields.append(field_name)

        elif change_type == "values_changed":
            # Type or property changes
            for path, change in changes.items():
                field_name = _extract_field_name(path)
                old_type = change.get('old_value', {}).get('type', 'unknown')
                new_type = change.get('new_value', {}).get('type', 'unknown')
                type_changes[field_name] = [old_type, new_type]

    migration_notes = _generate_migration_notes(added_fields, removed_fields, type_changes)

    return SchemaDiff(
        added_fields=added_fields,
        removed_fields=removed_fields,
        type_changes=type_changes,
        migration_notes=migration_notes
    )
```

## Schema Metadata Structure

### SchemaMetadata Model

```python
class SchemaMetadata(BaseModel):
    schema_id: str                    # {source_id}_v{version}_{uuid}
    source_id: str                    # Data source identifier
    version: int                      # Schema version number
    fields: List[SchemaField]         # Field definitions
    generated_at: datetime           # Creation timestamp
    compatible_dbs: List[str]        # ["mongodb"] or ["sqlite"] or both
    record_count: int                # Records used for inference
    extraction_stats: Dict[str, Union[int, float]]  # Processing statistics
    primary_key_candidates: Optional[List[str]] = None
    migration_notes: Optional[str] = None
    version_diff: Optional[Dict[str, Any]] = None  # DeepDiff results
    genson_schema: Optional[Dict[str, Any]] = None  # JSON Schema
```

### SchemaField Model

```python
class SchemaField(BaseModel):
    name: str                         # Field name
    path: Optional[str] = None        # Nested path (e.g., "user.address.city")
    type: str                         # Data type
    nullable: bool = True            # Whether field can be null
    example_value: Optional[Any] = None     # Sample value
    confidence: float = 1.0          # Type inference confidence
    source_offsets: Optional[List[int]] = None  # Source location hints
    suggested_index: bool = False    # SQLite index recommendation
```

## Performance Considerations

### Inference Optimization
- **Batch Processing**: Analyze multiple records together
- **Caching**: Cache type inference results
- **Sampling**: Use statistical sampling for large datasets

### Signature Computation
- **Normalization**: Consistent JSON serialization for hashing
- **Deterministic Ordering**: Sort keys for consistent signatures
- **Efficient Hashing**: SHA256 for collision resistance

### Memory Management
- **Streaming**: Process large files without full loading
- **Garbage Collection**: Clean up intermediate objects
- **Pagination**: Handle large schema histories

## Error Handling

### Inference Errors
- **Malformed Data**: Graceful handling of invalid JSON/values
- **Type Conflicts**: Automatic type promotion
- **Missing Data**: Null handling and confidence scoring

### Versioning Errors
- **Signature Conflicts**: Fallback to field-based comparison
- **Database Errors**: Transaction rollback and retry logic
- **Migration Failures**: Detailed error reporting and recovery

## Testing & Validation

### Schema Validation
- **Type Consistency**: Verify inferred types match actual data
- **Completeness**: Ensure all fields are captured
- **Accuracy**: Validate confidence scores against ground truth

### Versioning Validation
- **Determinism**: Same input produces same schema/version
- **Evolution Tracking**: Correct diff generation
- **Signature Uniqueness**: No false positives in duplicate detection

This dual-schema system ensures both fast pipeline operation and intelligent versioning while maintaining data integrity and evolution tracking.</content>
<parameter name="filePath">/home/yeashu/projects/dynamic-etl-pipeline/docs/schema_versioning.md