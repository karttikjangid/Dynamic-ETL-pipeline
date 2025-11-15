"""Schema persistence helpers."""

from __future__ import annotations

from typing import List, Optional

from pymongo import ASCENDING, DESCENDING
from pymongo.errors import PyMongoError

from core import SchemaMetadata
from utils.logger import get_logger


_LOGGER = get_logger(__name__)
_COLLECTION_NAME = "schemas"


def _get_collection(db):
    return db[_COLLECTION_NAME]


def _deserialize_schema(document: Optional[dict]) -> Optional[SchemaMetadata]:
    if not document:
        return None
    document.pop("_id", None)
    return SchemaMetadata(**document)


def store_schema(db, schema: SchemaMetadata) -> bool:
    """Persist schema metadata to the schema collection."""

    collection = _get_collection(db)
    payload = schema.dict()
    payload.update({"_id": schema.schema_id})
    try:
        collection.replace_one({"_id": schema.schema_id}, payload, upsert=True)
        return True
    except PyMongoError as exc:
        _LOGGER.error("Failed to store schema '%s': %s", schema.schema_id, exc)
        return False


def retrieve_schema(
    db, source_id: str, version: Optional[int] = None
) -> Optional[SchemaMetadata]:
    """Fetch a schema by source id and optional version."""

    collection = _get_collection(db)
    query = {"source_id": source_id}
    sort = [("version", DESCENDING)]
    if version is not None:
        query["version"] = version
        sort = None

    try:
        document = collection.find_one(query, sort=sort)
    except PyMongoError as exc:
        _LOGGER.error("Failed to retrieve schema for source '%s': %s", source_id, exc)
        return None

    return _deserialize_schema(document)


def get_schema_history(db, source_id: str) -> List[SchemaMetadata]:
    """Return all versions for a source."""

    collection = _get_collection(db)
    try:
        cursor = collection.find({"source_id": source_id}).sort("version", ASCENDING)
    except PyMongoError as exc:
        _LOGGER.error("Failed to fetch schema history for '%s': %s", source_id, exc)
        return []

    return [schema for schema in (_deserialize_schema(doc) for doc in cursor) if schema is not None]


def get_latest_schema_version(db, source_id: str) -> int:
    """Return the latest schema version for a source id."""

    collection = _get_collection(db)
    try:
        document = collection.find_one({"source_id": source_id}, sort=[("version", DESCENDING)])
    except PyMongoError as exc:
        _LOGGER.error("Failed to fetch latest schema version for '%s': %s", source_id, exc)
        return 0

    if not document:
        return 0

    version = document.get("version")
    return int(version) if isinstance(version, (int, float)) else 0
