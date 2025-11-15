"""Document retrieval helpers."""

from __future__ import annotations

from typing import Dict, List, Optional

from bson import ObjectId
from pymongo.errors import PyMongoError

from utils.logger import get_logger


_LOGGER = get_logger(__name__)


def get_documents(
    db, name: str, limit: int = 100, filter_query: Optional[Dict] = None
) -> List[Dict]:
    """Fetch a limited set of documents."""

    collection = db[name]
    query = filter_query or {}
    try:
        cursor = collection.find(query).limit(max(limit, 0))
        return list(cursor)
    except PyMongoError as exc:
        _LOGGER.error("Failed to retrieve documents from '%s': %s", name, exc)
        return []


def count_documents(db, name: str, filter_query: Optional[Dict] = None) -> int:
    """Return the count of documents matching a filter."""

    collection = db[name]
    query = filter_query or {}
    try:
        return collection.count_documents(query)
    except PyMongoError as exc:
        _LOGGER.error("Failed to count documents in '%s': %s", name, exc)
        return 0


def get_document_by_id(db, name: str, doc_id) -> Optional[Dict]:
    """Retrieve a document by its identifier."""

    if doc_id is None:
        return None

    collection = db[name]
    query_id = doc_id
    if isinstance(doc_id, str):
        try:
            query_id = ObjectId(doc_id)
        except (TypeError, ValueError):
            _LOGGER.warning("Invalid ObjectId string supplied: %s", doc_id)
            return None

    try:
        return collection.find_one({"_id": query_id})
    except PyMongoError as exc:
        _LOGGER.error("Failed to fetch document by id from '%s': %s", name, exc)
        return None
