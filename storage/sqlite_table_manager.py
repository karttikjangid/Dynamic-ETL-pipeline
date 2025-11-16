"""SQLite table manager for Tier-B structured data storage."""

from typing import List

from core.models import SchemaField
from storage.sqlite_connection import SQLiteConnection
from utils.logger import get_logger

logger = get_logger(__name__)


def create_table_from_schema(
    conn: SQLiteConnection,
    db_path: str,
    table_name: str,
    fields: List[SchemaField],
) -> bool:
    """Create a SQLite table from schema field definitions."""
    try:
        # Build CREATE TABLE statement
        columns = []
        
        # Add an auto-increment ID column
        columns.append("_id INTEGER PRIMARY KEY AUTOINCREMENT")
        
        # Add schema fields
        for field in fields:
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

        conn.execute(create_sql, db_path=db_path)
        logger.info(f"Created table '{table_name}' with {len(fields)} columns in {db_path}")

        # Create indexes for suggested fields
        for field in fields:
            if field.suggested_index:
                create_index(conn, db_path, table_name, field.name)

        return True
    except Exception as e:
        logger.error(f"Failed to create table '{table_name}': {e}")
        return False


def create_index(conn: SQLiteConnection, db_path: str, table_name: str, column_name: str) -> bool:
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
        conn.execute(index_sql, db_path=db_path)
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


def table_exists(conn: SQLiteConnection, db_path: str, table_name: str) -> bool:
    """Check if a table exists.
    
    Args:
        conn: SQLite connection
        table_name: Table name to check
        
    Returns:
        True if table exists
    """
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
        db_path=db_path,
    )
    return cursor.fetchone() is not None


def get_table_columns(conn: SQLiteConnection, db_path: str, table_name: str) -> List[str]:
    """Get list of column names in a table.
    
    Args:
        conn: SQLite connection
        table_name: Table name
        
    Returns:
        List of column names
    """
    cursor = conn.execute(f"PRAGMA table_info({table_name})", db_path=db_path)
    rows = cursor.fetchall()
    return [row[1] for row in rows]  # Column name is at index 1
