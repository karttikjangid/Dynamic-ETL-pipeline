"""Schema service helpers."""

from __future__ import annotations

from typing import Any, Dict, List, Union

from core import GetSchemaHistoryResponse, NormalizedRecord, SchemaMetadata
from inference.schema_generator import generate_schema


def compute_schema_for_source(
    fragments: Union[List[NormalizedRecord], List[Dict[str, Any]]], 
    source_id: str
) -> Dict[str, Any]:
    """
    Compute schema for a source from normalized fragments.
    
    This function serves as the bridge between the normalization pipeline
    and the schema generation layer. It:
    - Normalizes the calling context (accepts both NormalizedRecord and dict)
    - Extracts the data payload from records
    - Delegates to schema_generator.generate_schema()
    - Returns the schema as a dictionary
    
    This function is pure computation - it does NOT perform any storage
    operations. Storage/persistence should be handled by the caller.
    
    Args:
        fragments: Either a list of NormalizedRecord objects (from the 
                  normalization pipeline) or a list of dictionaries 
                  (already extracted data). The function will normalize 
                  both input types.
        source_id: Identifier for the data source (e.g., "user_api", 
                  "orders_csv"). Used for schema tracking and versioning.
    
    Returns:
        A dictionary containing the computed schema with keys:
        - schema_id: Unique identifier for this schema version
        - source_id: The source identifier passed in
        - version: Schema version number
        - fields: List of field definitions (name, type, nullable, etc.)
        - generated_at: Timestamp when schema was generated
        - record_count: Number of records analyzed
        - extraction_stats: Statistics about the data extraction
        - compatible_dbs: List of compatible database systems
    
    Example:
        >>> # From normalization pipeline
        >>> normalized = normalize_all_records(extracted_records)
        >>> schema = compute_schema_for_source(normalized, "user_api")
        >>> 
        >>> # From already-extracted data
        >>> data = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
        >>> schema = compute_schema_for_source(data, "users")
        >>> 
        >>> # Schema is ready for storage (but not stored by this function)
        >>> schema_store.save(schema)  # Caller's responsibility
    
    Note:
        - This function does NOT save to database/storage
        - This function does NOT handle schema versioning logic
        - This function does NOT perform schema evolution/migration
        - All persistence operations are the caller's responsibility
        
        For full schema lifecycle management, use the higher-level
        pipeline orchestrators that call this function.
    """
    # Normalize input: extract data from NormalizedRecord objects
    records = []
    
    if not fragments:
        # Empty input, pass empty list to generator
        records = []
    elif isinstance(fragments[0], NormalizedRecord):
        # Extract .data from each NormalizedRecord
        records = [frag.data for frag in fragments]
    elif isinstance(fragments[0], dict):
        # Already in dict format
        records = fragments
    else:
        # Unknown type, try to coerce
        records = [dict(frag) if hasattr(frag, '__dict__') else frag for frag in fragments]
    
    # Delegate to schema generator
    schema_metadata = generate_schema(records, source_id)
    
    # Convert SchemaMetadata to dict for flexible return type
    return schema_metadata.model_dump()


def get_current_schema(source_id: str) -> SchemaMetadata:
    """Return the latest schema for a source."""

    raise NotImplementedError


def get_schema_history(source_id: str) -> GetSchemaHistoryResponse:
    """Return all schema versions plus diffs."""

    raise NotImplementedError


def handle_schema_evolution(
    source_id: str, old_schema: SchemaMetadata, new_schema: SchemaMetadata
) -> bool:
    """Apply schema evolution procedures when needed."""

    raise NotImplementedError
