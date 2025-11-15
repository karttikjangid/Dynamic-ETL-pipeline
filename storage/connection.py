"""MongoDB connection manager."""

from __future__ import annotations

from threading import Lock
from typing import Optional

from pymongo import MongoClient

from config import get_settings


class MongoConnection:
    """Singleton-style MongoDB connection helper."""

    _instance: Optional["MongoConnection"] = None
    _lock: Lock = Lock()

    def __init__(self, uri: Optional[str] = None) -> None:
        self._settings = get_settings()
        self._uri = uri or self._settings.mongodb_uri
        self._client: Optional[MongoClient] = None

    def connect(self) -> MongoClient:
        """Establish a new Mongo client."""

        if self._client is None:
            self._client = MongoClient(self._uri)
        return self._client

    def disconnect(self) -> None:
        """Close the Mongo client if present."""

        if self._client is not None:
            self._client.close()
            self._client = None

    def get_client(self) -> MongoClient:
        """Return the active Mongo client, connecting if necessary."""

        if self._client is None:
            return self.connect()
        return self._client

    def get_database(self, name: str):
        """Return a database reference from the Mongo client."""

        client = self.get_client()
        return client[name]

    @staticmethod
    def get_instance() -> "MongoConnection":
        """Return the shared MongoConnection instance."""

        if MongoConnection._instance is None:
            with MongoConnection._lock:
                if MongoConnection._instance is None:
                    MongoConnection._instance = MongoConnection()
        return MongoConnection._instance
