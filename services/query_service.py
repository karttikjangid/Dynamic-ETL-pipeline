"""Strict query execution service."""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, Sequence, Tuple

from bson import ObjectId
from pymongo.errors import PyMongoError

from core import QueryResult
from core.exceptions import QueryExecutionError
from services import orchestrator as service_orchestrator
from storage.connection import MongoConnection
from utils.logger import get_logger


LOGGER = get_logger(__name__)
DEFAULT_LIMIT = 100
MAX_LIMIT = 1000


def execute_query(source_id: str, query: Dict[str, Any]) -> QueryResult:
    """Execute a strict Mongo/SQL-style query and return results."""

    filter_query, limit, sort_spec = _normalize_query_payload(query)
    db_name, collection_name = service_orchestrator.get_db_and_collection(source_id)
    db = MongoConnection.get_instance().get_database(db_name)
    collection = db[collection_name]

    started = time.perf_counter()
    try:
        cursor = collection.find(filter_query)
        if sort_spec:
            cursor = cursor.sort(sort_spec)
        cursor = cursor.limit(limit)
        documents = list(cursor)
    except PyMongoError as exc:  # pragma: no cover - depends on Mongo
        LOGGER.error("Query failed for '%s': %s", source_id, exc)
        raise QueryExecutionError("Query execution failed") from exc

    elapsed_ms = (time.perf_counter() - started) * 1000
    serialized_docs = _serialize_documents(documents)

    return QueryResult(
        query={"filter": filter_query, "limit": limit, "sort": sort_spec},
        results=serialized_docs,
        result_count=len(serialized_docs),
        execution_time_ms=elapsed_ms,
    )


def _normalize_query_payload(query: Dict[str, Any]) -> Tuple[Dict[str, Any], int, Optional[List[Tuple[str, int]]]]:
    if not isinstance(query, dict):
        raise QueryExecutionError("Query payload must be a dictionary")

    filter_query = query.get("filter", {})
    if filter_query is None:
        filter_query = {}
    if not isinstance(filter_query, dict):
        raise QueryExecutionError("Query 'filter' must be a dictionary")

    limit = query.get("limit", DEFAULT_LIMIT)
    try:
        limit_value = int(limit)
    except (TypeError, ValueError):
        raise QueryExecutionError("Query 'limit' must be an integer") from None
    limit_value = max(0, min(limit_value, MAX_LIMIT))

    sort_spec = _normalize_sort(query.get("sort"))
    return filter_query, limit_value, sort_spec


def _normalize_sort(sort_value: Any) -> Optional[List[Tuple[str, int]]]:
    if sort_value in (None, [], ()):  # allow falsy sorts
        return None

    if not isinstance(sort_value, (list, tuple)):
        raise QueryExecutionError("Query 'sort' must be a list of field/direction pairs")

    normalized: List[Tuple[str, int]] = []
    for entry in sort_value:
        field: Optional[str] = None
        direction: Any = 1
        if isinstance(entry, (list, tuple)) and len(entry) == 2:
            field = str(entry[0])
            direction = entry[1]
        elif isinstance(entry, dict) and len(entry) == 1:
            field, direction = next(iter(entry.items()))
        else:
            raise QueryExecutionError("Invalid sort entry; expected [field, direction]")

        if not field:
            raise QueryExecutionError("Sort field cannot be empty")

        direction_value = _normalize_sort_direction(direction)
        normalized.append((field, direction_value))

    return normalized


def _normalize_sort_direction(direction: Any) -> int:
    if direction in (1, "asc", "ASC", "ascending"):
        return 1
    if direction in (-1, "desc", "DESC", "descending"):
        return -1
    raise QueryExecutionError("Sort direction must be 1/-1 or asc/desc")


def _serialize_documents(documents: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    serialized: List[Dict[str, Any]] = []
    for doc in documents:
        prepared = dict(doc)
        identifier = prepared.get("_id")
        if isinstance(identifier, ObjectId):
            prepared["_id"] = str(identifier)
        elif identifier is not None:
            prepared["_id"] = str(identifier)
        serialized.append(prepared)
    return serialized
