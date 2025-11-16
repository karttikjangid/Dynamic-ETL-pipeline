"""Storage router - decides MongoDB vs SQLite based on data shape."""

from typing import Any, Dict, List

from core.models import NormalizedRecord, SchemaMetadata
from utils.logger import get_logger

logger = get_logger(__name__)


def categorize_records_by_storage(
    records: List[NormalizedRecord]
) -> Dict[str, List[NormalizedRecord]]:
    """Categorize records into MongoDB vs SQLite based on source_type.
    
    Storage Strategy:
    - MongoDB: json, yaml_block (nested/unstructured)
    - SQLite: html_table, csv_block, kv (flat/tabular)
    
    Args:
        records: List of normalized records
        
    Returns:
        Dict with keys 'mongodb' and 'sqlite', each containing list of records
    """
    mongodb_records = []
    sqlite_records = []
    
    for record in records:
        source_type = record.source_type
        
        # Route based on source type
        if source_type in ["json", "yaml_block"]:
            # Unstructured/nested -> MongoDB
            mongodb_records.append(record)
        elif source_type in ["html_table", "csv_block", "kv"]:
            # Structured/tabular -> SQLite
            sqlite_records.append(record)
        else:
            # Default: check data shape
            if _is_flat_structure(record.data):
                sqlite_records.append(record)
            else:
                mongodb_records.append(record)
    
    logger.info(
        f"Categorized {len(records)} records: "
        f"{len(mongodb_records)} MongoDB, {len(sqlite_records)} SQLite"
    )
    
    return {
        "mongodb": mongodb_records,
        "sqlite": sqlite_records
    }


def _is_flat_structure(data: Dict[str, Any]) -> bool:
    """Check if data structure is flat (no nested dicts/lists).
    
    Args:
        data: Data dict to check
        
    Returns:
        True if flat structure
    """
    for value in data.values():
        if isinstance(value, dict):
            return False
        if isinstance(value, list) and value and isinstance(value[0], dict):
            return False
    
    return True


def should_use_sqlite(source_type: str) -> bool:
    """Determine if a source type should use SQLite.
    
    Args:
        source_type: Type of source data
        
    Returns:
        True if SQLite should be used
    """
    sqlite_types = ["html_table", "csv_block", "kv"]
    return source_type in sqlite_types


def get_compatible_dbs_for_schema(schema: SchemaMetadata) -> List[str]:
    """Determine which databases are compatible with a schema.
    
    Args:
        schema: Schema metadata
        
    Returns:
        List of compatible database names
    """
    compatible = []
    
    # Check if schema is flat enough for SQLite
    is_flat = all(
        field.type not in ["object", "array"]
        for field in schema.fields
    )
    
    if is_flat:
        compatible.append("sqlite")
    
    # MongoDB can handle anything
    compatible.append("mongodb")
    
    return compatible
