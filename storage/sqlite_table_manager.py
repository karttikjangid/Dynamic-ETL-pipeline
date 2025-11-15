"""SQLite table manager for Tier-B structured data storage."""

from typing import Any, Dict, List, Optional

from core.models import SchemaMetadata, SchemaField
from storage.sqlite_connection import SQLiteConnection
from utils.logger import get_logger

logger = get_logger(__name__)


def create_table_from_schema(
    conn: SQLiteConnection,
    table_name: str,
    schema: SchemaMetadata
) -> bool:
    """Create a SQLite table from schema metadata.
    
    Args:
        conn: SQLite connection
        table_name: Name of table to create
        schema: Schema metadata with field definitions
        
    Returns:
        True if successful
    """
    try:
        # Build CREATE TABLE statement
        columns = []
        
        # Add an auto-increment ID column
        columns.append("_id INTEGER PRIMARY KEY AUTOINCREMENT")
        
        # Add schema fields
        for field in schema.fields:
            col_name = field.name
            col_type = _map_type_to_sqlite(field.type)
            nullable = "NULL" if field.nullable else "NOT NULL"
            
            columns.append(f"{col_name} {col_type} {nullable}")
        
        # Add metadata columns
        columns.append("_source_id TEXT")
        columns.append("_ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        
        create_sql = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            {', '.join(columns)}
        )
        """
        
        conn.execute(create_sql)
        logger.info(f"Created table '{table_name}' with {len(schema.fields)} columns")
        
        # Create indexes for suggested fields
        for field in schema.fields:
            if field.suggested_index:
                create_index(conn, table_name, field.name)
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to create table '{table_name}': {e}")
        return False


def create_index(conn: SQLiteConnection, table_name: str, column_name: str) -> bool:
    """Create an index on a table column.
    
    Args:
        conn: SQLite connection
        table_name: Table name
        column_name: Column to index
        
    Returns:
        True if successful
    """
    try:
        index_name = f"idx_{table_name}_{column_name}"
        index_sql = f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name}({column_name})"
        conn.execute(index_sql)
        logger.info(f"Created index '{index_name}'")
        return True
    except Exception as e:
        logger.warning(f"Failed to create index on {table_name}.{column_name}: {e}")
        return False


def _map_type_to_sqlite(field_type: str) -> str:
    """Map schema field type to SQLite type.
    
    Args:
        field_type: Field type from schema
        
    Returns:
        SQLite type string
    """
    type_mapping = {
        "string": "TEXT",
        "integer": "INTEGER",
        "number": "REAL",
        "float": "REAL",
        "boolean": "INTEGER",  # SQLite uses 0/1 for boolean
        "datetime": "TIMESTAMP",
        "date": "DATE",
        "object": "TEXT",  # Store as JSON
        "array": "TEXT",   # Store as JSON
        "null": "TEXT"
    }
    
    return type_mapping.get(field_type.lower(), "TEXT")


def get_table_name(source_id: str, version: int) -> str:
    """Generate versioned table name.
    
    Args:
        source_id: Source identifier
        version: Schema version
        
    Returns:
        Table name like "source_id_v1"
    """
    # Sanitize source_id for SQL
    safe_source_id = source_id.replace("-", "_").replace(".", "_")
    return f"{safe_source_id}_v{version}"


def table_exists(conn: SQLiteConnection, table_name: str) -> bool:
    """Check if a table exists.
    
    Args:
        conn: SQLite connection
        table_name: Table name to check
        
    Returns:
        True if table exists
    """
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,)
    )
    return cursor.fetchone() is not None


def get_table_columns(conn: SQLiteConnection, table_name: str) -> List[str]:
    """Get list of column names in a table.
    
    Args:
        conn: SQLite connection
        table_name: Table name
        
    Returns:
        List of column names
    """
    cursor = conn.execute(f"PRAGMA table_info({table_name})")
    rows = cursor.fetchall()
    return [row[1] for row in rows]  # Column name is at index 1
