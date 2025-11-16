"""SQLite connection manager for structured data storage."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from threading import Lock
from typing import Dict, Optional

from config import get_settings


class SQLiteConnection:
    """Singleton-style SQLite connection helper for ETL pipeline."""

    _instance: Optional["SQLiteConnection"] = None
    _lock: Lock = Lock()

    def __init__(self, db_path: Optional[str] = None) -> None:
        """Initialize SQLite connection manager.

        Args:
            db_path: Optional default database path. Additional per-version paths
                will be opened on demand.
        """
        self._settings = get_settings()

        if db_path is None:
            default_path = Path(self._settings.sqlite_db_path).expanduser()
            default_path.parent.mkdir(parents=True, exist_ok=True)
            db_path = str(default_path)

        self._default_path = db_path
        self._connections: Dict[str, sqlite3.Connection] = {}

    def connect(self, db_path: Optional[str] = None) -> sqlite3.Connection:
        """Establish (or reuse) a SQLite connection for a given db path."""

        target = db_path or self._default_path
        if target in self._connections:
            return self._connections[target]

        Path(target).parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(
            target,
            check_same_thread=False,
            isolation_level=None,
        )
        connection.execute("PRAGMA foreign_keys = ON")
        connection.row_factory = sqlite3.Row
        self._connections[target] = connection
        return connection

    def disconnect(self, db_path: Optional[str] = None) -> None:
        """Close one or all SQLite connections."""

        if db_path:
            connection = self._connections.pop(db_path, None)
            if connection is not None:
                connection.close()
            return

        for connection in self._connections.values():
            connection.close()
        self._connections.clear()

    def get_connection(self, db_path: Optional[str] = None) -> sqlite3.Connection:
        """Return a SQLite connection for the provided path."""

        return self.connect(db_path)

    def execute(self, query: str, params: Optional[tuple] = None, db_path: Optional[str] = None) -> sqlite3.Cursor:
        """Execute a query with optional parameters.

        Args:
            query: SQL query string
            params: Optional tuple of parameters for parameterized queries
            db_path: Database file path. Defaults to shared database file.
            
        Returns:
            Cursor object with query results
        """
        conn = self.get_connection(db_path)
        if params:
            return conn.execute(query, params)
        return conn.execute(query)

    def executemany(
        self,
        query: str,
        params_list: list,
        db_path: Optional[str] = None,
    ) -> sqlite3.Cursor:
        """Execute a query with multiple parameter sets.

        Args:
            query: SQL query string
            params_list: List of parameter tuples
            db_path: Database file path
            
        Returns:
            Cursor object
        """
        conn = self.get_connection(db_path)
        return conn.executemany(query, params_list)

    def commit(self, db_path: Optional[str] = None) -> None:
        """Commit current transaction for a connection."""

        connection = self._connections.get(db_path or self._default_path)
        if connection:
            connection.commit()

    def rollback(self, db_path: Optional[str] = None) -> None:
        """Rollback current transaction for a connection."""

        connection = self._connections.get(db_path or self._default_path)
        if connection:
            connection.rollback()

    @staticmethod
    def get_instance() -> "SQLiteConnection":
        """Return the shared SQLiteConnection instance."""
        if SQLiteConnection._instance is None:
            with SQLiteConnection._lock:
                if SQLiteConnection._instance is None:
                    SQLiteConnection._instance = SQLiteConnection()
        return SQLiteConnection._instance
