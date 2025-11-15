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

        raise NotImplementedError

    def disconnect(self) -> None:
        """Close the Mongo client if present."""

        raise NotImplementedError

    def get_client(self) -> MongoClient:
        """Return the active Mongo client, connecting if necessary."""

        raise NotImplementedError

    def get_database(self, name: str):
        """Return a database reference from the Mongo client."""

        raise NotImplementedError

    @staticmethod
    def get_instance() -> "MongoConnection":
        """Return the shared MongoConnection instance."""

        raise NotImplementedError
