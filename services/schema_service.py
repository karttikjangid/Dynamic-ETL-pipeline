"""Schema service helpers."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union, cast

from core import GetSchemaHistoryResponse, NormalizedRecord, SchemaMetadata
from core.exceptions import SchemaInferenceError, StorageError
from inference.schema_generator import generate_schema
from services import orchestrator as service_orchestrator
from storage import migration, schema_store
from storage.connection import MongoConnection
from utils.logger import get_logger


LOGGER = get_logger(__name__)


def _get_db_for_source(source_id: str):
    """Return the Mongo database handle for a given source id."""

    db_name, _ = service_orchestrator.get_db_and_collection(source_id)
    connection = MongoConnection.get_instance()
    return connection.get_database(db_name)


def compute_schema_for_source(
    fragments: Union[List[NormalizedRecord], List[Dict[str, Any]]],
    source_id: str,
) -> SchemaMetadata:
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
        SchemaMetadata instance describing the inferred schema.
    
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
    records: List[Dict[str, Any]] = []
    
    if not fragments:
        # Empty input, pass empty list to generator
        records = []
    elif isinstance(fragments[0], NormalizedRecord):
        # Extract .data from each NormalizedRecord
        normalized = cast(List[NormalizedRecord], fragments)
        records = [frag.data for frag in normalized]
    elif isinstance(fragments[0], dict):
        # Already in dict format
        records = cast(List[Dict[str, Any]], fragments)
    else:
        # Unknown type, try to coerce
        coerced: List[Dict[str, Any]] = []
        for frag in fragments:
            if hasattr(frag, "dict"):
                coerced.append(getattr(frag, "dict")())
            elif hasattr(frag, "__dict__"):
                coerced.append(dict(getattr(frag, "__dict__")))
            elif isinstance(frag, dict):
                coerced.append(frag)
            else:
                coerced.append({"value": frag})
        records = coerced
    
    # Delegate to schema generator
    return generate_schema(records, source_id)


def get_current_schema(source_id: str) -> SchemaMetadata:
    """Return the latest schema for a source."""

    db = _get_db_for_source(source_id)
    schema = schema_store.retrieve_schema(db, source_id)
    if schema is None:
        raise SchemaInferenceError(f"No schema found for source '{source_id}'")
    return schema


def get_schema_history(source_id: str) -> GetSchemaHistoryResponse:
    """Return all schema versions plus diffs."""

    db = _get_db_for_source(source_id)
    schemas = schema_store.get_schema_history(db, source_id)
    diffs = []
    if len(schemas) > 1:
        for previous, current in zip(schemas, schemas[1:]):
            diffs.append(migration.detect_schema_change(previous, current))
    return GetSchemaHistoryResponse(schemas=schemas, diffs=diffs)


def handle_schema_evolution(
    source_id: str, old_schema: SchemaMetadata, new_schema: SchemaMetadata
) -> bool:
    """Apply schema evolution procedures when needed."""

    if old_schema is None or new_schema is None:
        return False

    diff = migration.detect_schema_change(old_schema, new_schema)
    if not diff.added_fields and not diff.removed_fields and not diff.type_changes:
        LOGGER.info("No schema evolution required for source '%s'", source_id)
        return False

    db_name, collection_name = service_orchestrator.get_db_and_collection(source_id)
    db = MongoConnection.get_instance().get_database(db_name)
    success = migration.evolve_collection_schema(db, collection_name, old_schema, new_schema)
    if not success:
        raise StorageError(f"Failed to evolve schema for source '{source_id}'")
    return True
