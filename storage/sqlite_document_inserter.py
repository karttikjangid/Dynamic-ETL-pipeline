"""SQLite document inserter with nested object flattening."""

import json
from typing import Any, Dict, List, Optional

from core.models import SchemaMetadata
from storage.sqlite_connection import SQLiteConnection
from storage.sqlite_table_manager import get_table_columns
from utils.logger import get_logger

logger = get_logger(__name__)


def insert_documents_sqlite(
    conn: SQLiteConnection,
    table_name: str,
    documents: List[Dict[str, Any]],
    source_id: str,
    schema: Optional[SchemaMetadata] = None
) -> int:
    """Insert documents into SQLite table with flattening.
    
    Args:
        conn: SQLite connection
        table_name: Target table name
        documents: List of documents to insert
        source_id: Source identifier
        schema: Optional schema for validation
        
    Returns:
        Number of documents inserted
    """
    if not documents:
        return 0
    
    # Get table columns
    columns = get_table_columns(conn, table_name)
    
    # Remove metadata columns from consideration
    data_columns = [c for c in columns if not c.startswith('_')]
    
    inserted_count = 0
    
    for doc in documents:
        try:
            # Flatten nested document
            flattened = flatten_document(doc)
            
            # Prepare values for insertion
            values = {}
            for col in data_columns:
                if col in flattened:
                    values[col] = serialize_value(flattened[col])
                else:
                    values[col] = None
            
            # Add metadata
            values['_source_id'] = source_id
            
            # Build INSERT statement
            col_names = list(values.keys())
            placeholders = ', '.join(['?' for _ in col_names])
            col_list = ', '.join(col_names)
            
            insert_sql = f"INSERT INTO {table_name} ({col_list}) VALUES ({placeholders})"
            conn.execute(insert_sql, tuple(values.values()))
            
            inserted_count += 1
            
        except Exception as e:
            logger.warning(f"Failed to insert document into {table_name}: {e}")
            continue
    
    logger.info(f"Inserted {inserted_count}/{len(documents)} documents into {table_name}")
    return inserted_count


def flatten_document(doc: Dict[str, Any], prefix: str = "", sep: str = "_") -> Dict[str, Any]:
    """Flatten a nested dictionary.
    
    Args:
        doc: Document with potential nested dicts
        prefix: Key prefix for recursion
        sep: Separator for nested keys
        
    Returns:
        Flattened dict with keys like "parent_child"
    """
    flattened = {}
    
    for key, value in doc.items():
        new_key = f"{prefix}{sep}{key}" if prefix else key
        
        if isinstance(value, dict):
            # Recursively flatten nested dict
            nested = flatten_document(value, prefix=new_key, sep=sep)
            flattened.update(nested)
        elif isinstance(value, list):
            # Store arrays as JSON strings
            flattened[new_key] = value
        else:
            flattened[new_key] = value
    
    return flattened


def serialize_value(value: Any) -> Any:
    """Serialize a value for SQLite storage.
    
    Args:
        value: Value to serialize
        
    Returns:
        Serialized value suitable for SQLite
    """
    if value is None:
        return None
    
    # Handle booleans
    if isinstance(value, bool):
        return 1 if value else 0
    
    # Handle lists and dicts (store as JSON)
    if isinstance(value, (list, dict)):
        return json.dumps(value)
    
    # Handle other types
    return value


def batch_insert_documents_sqlite(
    conn: SQLiteConnection,
    table_name: str,
    documents: List[Dict[str, Any]],
    source_id: str,
    batch_size: int = 100
) -> int:
    """Batch insert documents for better performance.
    
    Args:
        conn: SQLite connection
        table_name: Target table name
        documents: List of documents to insert
        source_id: Source identifier
        batch_size: Number of documents per batch
        
    Returns:
        Total number of documents inserted
    """
    total_inserted = 0
    
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i + batch_size]
        count = insert_documents_sqlite(conn, table_name, batch, source_id)
        total_inserted += count
    
    return total_inserted
