"""SQLite connection manager for structured data storage."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from threading import Lock
from typing import Optional

from config import get_settings


class SQLiteConnection:
    """Singleton-style SQLite connection helper for ETL pipeline."""

    _instance: Optional["SQLiteConnection"] = None
    _lock: Lock = Lock()

    def __init__(self, db_path: Optional[str] = None) -> None:
        """Initialize SQLite connection manager.
        
        Args:
            db_path: Path to SQLite database file. If None, uses default from settings.
        """
        self._settings = get_settings()
        
        if db_path is None:
            # Default: create a data directory and use etl_pipeline.db
            data_dir = Path("./data/sqlite")
            data_dir.mkdir(parents=True, exist_ok=True)
            db_path = str(data_dir / "etl_pipeline.db")
        
        self._db_path = db_path
        self._connection: Optional[sqlite3.Connection] = None

    def connect(self) -> sqlite3.Connection:
        """Establish a new SQLite connection."""
        if self._connection is None:
            self._connection = sqlite3.connect(
                self._db_path,
                check_same_thread=False,  # Allow multi-threaded access
                isolation_level=None  # Autocommit mode
            )
            # Enable foreign keys
            self._connection.execute("PRAGMA foreign_keys = ON")
            # Use Row factory for dict-like access
            self._connection.row_factory = sqlite3.Row
        return self._connection

    def disconnect(self) -> None:
        """Close the SQLite connection if present."""
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    def get_connection(self) -> sqlite3.Connection:
        """Return the active SQLite connection, connecting if necessary."""
        if self._connection is None:
            return self.connect()
        return self._connection

    def execute(self, query: str, params: Optional[tuple] = None) -> sqlite3.Cursor:
        """Execute a query with optional parameters.
        
        Args:
            query: SQL query string
            params: Optional tuple of parameters for parameterized queries
            
        Returns:
            Cursor object with query results
        """
        conn = self.get_connection()
        if params:
            return conn.execute(query, params)
        return conn.execute(query)

    def executemany(self, query: str, params_list: list) -> sqlite3.Cursor:
        """Execute a query with multiple parameter sets.
        
        Args:
            query: SQL query string
            params_list: List of parameter tuples
            
        Returns:
            Cursor object
        """
        conn = self.get_connection()
        return conn.executemany(query, params_list)

    def commit(self) -> None:
        """Commit current transaction."""
        if self._connection:
            self._connection.commit()

    def rollback(self) -> None:
        """Rollback current transaction."""
        if self._connection:
            self._connection.rollback()

    @staticmethod
    def get_instance() -> "SQLiteConnection":
        """Return the shared SQLiteConnection instance."""
        if SQLiteConnection._instance is None:
            with SQLiteConnection._lock:
                if SQLiteConnection._instance is None:
                    SQLiteConnection._instance = SQLiteConnection()
        return SQLiteConnection._instance
