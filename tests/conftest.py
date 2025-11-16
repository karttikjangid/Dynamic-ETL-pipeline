"""Shared pytest fixtures for the Dynamic ETL Pipeline tests."""

from __future__ import annotations

import os
from typing import Generator

import mongomock
import pytest

os.environ.setdefault("ETL_MONGODB_URI", "mongodb://localhost:27017")

from services import pipeline_service
from storage.connection import MongoConnection
from storage.sqlite_connection import SQLiteConnection


class _FakeMongoConnection:
    """Lightweight stand-in for the real MongoConnection singleton."""

    def __init__(self, client: mongomock.MongoClient):
        self._client = client

    def get_database(self, name: str):
        return self._client[name]

    def get_client(self):
        return self._client

    def connect(self):  # pragma: no cover - compatibility shim
        return self._client

    def disconnect(self):  # pragma: no cover - compatibility shim
        return None


@pytest.fixture(autouse=True)
def mock_mongo_connection(monkeypatch) -> Generator[mongomock.MongoClient, None, None]:
    """Provide an in-memory MongoDB for every test."""

    client = mongomock.MongoClient()
    fake_connection = _FakeMongoConnection(client)

    monkeypatch.setattr(
        MongoConnection,
        "get_instance",
        staticmethod(lambda: fake_connection),
    )

    yield client


@pytest.fixture(autouse=True)
def stub_collection_creation(monkeypatch):
    """Avoid calling unsupported Mongo admin commands under mongomock."""

    def _noop_create_collection(db, name, schema):
        db[name]  # ensure collection handle exists
        return True

    monkeypatch.setattr(
        pipeline_service.collection_manager,
        "create_collection_from_schema",
        _noop_create_collection,
    )


@pytest.fixture(autouse=True)
def isolated_sqlite_connection(monkeypatch, tmp_path):
    """Provide a fresh SQLite database per test and override the singleton."""

    db_path = tmp_path / "etl_pipeline.sqlite"
    connection = SQLiteConnection(db_path=str(db_path))

    monkeypatch.setattr(
        SQLiteConnection,
        "get_instance",
        staticmethod(lambda: connection),
    )

    yield connection

    connection.disconnect()