"""Strict query execution service."""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, Sequence, Tuple

from bson import ObjectId
from pymongo.errors import PyMongoError

from core import QueryResult
from core.exceptions import QueryExecutionError, SchemaInferenceError
from services import orchestrator as service_orchestrator, schema_service
from storage.connection import MongoConnection
from storage.sqlite_connection import SQLiteConnection
from storage.sqlite_table_manager import get_table_columns, get_table_name, table_exists
from utils.logger import get_logger


LOGGER = get_logger(__name__)
DEFAULT_LIMIT = 100
MAX_LIMIT = 1000
SQLITE_SUPPORTED_OPERATORS = {"$eq", "$ne", "$gt", "$gte", "$lt", "$lte", "$in", "$like"}


def execute_query(source_id: str, query: Dict[str, Any]) -> QueryResult:
    """Execute a strict query against MongoDB or SQLite based on the payload."""

    if not isinstance(query, dict):
        raise QueryExecutionError("Query payload must be a dictionary")

    engine_value = query.get("engine", "mongodb")
    if not isinstance(engine_value, str):
        raise QueryExecutionError("engine must be a string if provided")

    engine = engine_value.lower()
    payload = {k: v for k, v in query.items() if k != "engine"}

    if engine == "sqlite":
        return _execute_sqlite_query(source_id, payload)

    if engine != "mongodb":
        raise QueryExecutionError("Unsupported query engine. Use 'mongodb' or 'sqlite'.")

    return _execute_mongodb_query(source_id, payload)


def _execute_mongodb_query(source_id: str, query: Dict[str, Any]) -> QueryResult:
    filter_query, limit, sort_spec = _normalize_mongo_query_payload(query)
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
        query={"engine": "mongodb", "filter": filter_query, "limit": limit, "sort": sort_spec},
        results=serialized_docs,
        result_count=len(serialized_docs),
        execution_time_ms=elapsed_ms,
    )


def _execute_sqlite_query(source_id: str, query: Dict[str, Any]) -> QueryResult:
    try:
        schema = schema_service.get_current_schema(source_id)
    except SchemaInferenceError as exc:
        raise QueryExecutionError(str(exc)) from exc

    if "sqlite" not in (schema.compatible_dbs or []):
        raise QueryExecutionError("Source is not stored in SQLite.")

    table_name = get_table_name(source_id, schema.version)
    conn = SQLiteConnection.get_instance()
    if not table_exists(conn, table_name):
        raise QueryExecutionError("SQLite table for source does not exist.")

    columns = get_table_columns(conn, table_name)
    select_clause = _build_select_clause(query.get("select"), columns)
    where_clause, params = _build_where_clause(query.get("where"), columns)
    order_clause = _build_order_by_clause(query.get("order_by"), columns)
    limit = _normalize_limit(query.get("limit", DEFAULT_LIMIT))

    sql_parts = [f"SELECT {select_clause} FROM {table_name}"]
    if where_clause:
        sql_parts.append(f"WHERE {where_clause}")
    if order_clause:
        sql_parts.append(f"ORDER BY {order_clause}")
    sql_parts.append("LIMIT ?")
    params.append(limit)
    sql = " ".join(sql_parts)

    started = time.perf_counter()
    cursor = conn.execute(sql, tuple(params))
    rows = cursor.fetchall()
    elapsed_ms = (time.perf_counter() - started) * 1000

    results = [dict(row) for row in rows]
    return QueryResult(
        query={
            "engine": "sqlite",
            "sql": sql,
            "select": query.get("select"),
            "where": query.get("where"),
            "order_by": query.get("order_by"),
            "limit": limit,
        },
        results=results,
        result_count=len(results),
        execution_time_ms=elapsed_ms,
    )


def _normalize_mongo_query_payload(query: Dict[str, Any]) -> Tuple[Dict[str, Any], int, Optional[List[Tuple[str, int]]]]:
    filter_query = query.get("filter", {})
    if filter_query is None:
        filter_query = {}
    if not isinstance(filter_query, dict):
        raise QueryExecutionError("Query 'filter' must be a dictionary")

    limit_value = _normalize_limit(query.get("limit", DEFAULT_LIMIT), allow_zero=True)
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


def _normalize_limit(value: Any, allow_zero: bool = False) -> int:
    try:
        limit_value = int(value)
    except (TypeError, ValueError):
        raise QueryExecutionError("Query 'limit' must be an integer") from None

    minimum = 0 if allow_zero else 1
    limit_value = max(minimum, min(limit_value, MAX_LIMIT))
    return limit_value


def _build_select_clause(select_fields: Any, allowed_columns: List[str]) -> str:
    if select_fields is None:
        return "*"
    if not isinstance(select_fields, (list, tuple)) or not select_fields:
        raise QueryExecutionError("'select' must be a non-empty list of column names")

    normalized: List[str] = []
    for field in select_fields:
        if not isinstance(field, str):
            raise QueryExecutionError("select entries must be strings")
        if field not in allowed_columns:
            raise QueryExecutionError(f"Column '{field}' is not available in SQLite table")
        normalized.append(field)
    return ", ".join(normalized)


def _build_where_clause(where_clause: Any, allowed_columns: List[str]) -> Tuple[str, List[Any]]:
    if where_clause in (None, {}):
        return "", []
    if not isinstance(where_clause, dict):
        raise QueryExecutionError("'where' must be a dictionary")

    fragments: List[str] = []
    params: List[Any] = []

    for column, value in where_clause.items():
        if not isinstance(column, str) or column not in allowed_columns:
            raise QueryExecutionError(f"Column '{column}' is not available in SQLite table")

        clause, clause_params = _render_condition(column, value)
        fragments.append(clause)
        params.extend(clause_params)

    return " AND ".join(fragments), params


def _render_condition(column: str, value: Any) -> Tuple[str, List[Any]]:
    if isinstance(value, dict):
        if not value:
            raise QueryExecutionError(f"Operator dict for column '{column}' cannot be empty")
        sub_clauses = []
        params: List[Any] = []
        for operator, op_value in value.items():
            if operator not in SQLITE_SUPPORTED_OPERATORS:
                raise QueryExecutionError(f"Unsupported operator '{operator}' for SQLite queries")
            clause, clause_params = _render_operator(column, operator, op_value)
            sub_clauses.append(clause)
            params.extend(clause_params)
        combined = " AND ".join(sub_clauses)
        if len(sub_clauses) > 1:
            combined = f"({combined})"
        return combined, params

    # Default equality
    return f"{column} = ?", [value]


def _render_operator(column: str, operator: str, value: Any) -> Tuple[str, List[Any]]:
    if operator == "$in":
        if not isinstance(value, (list, tuple)) or not value:
            raise QueryExecutionError("$in requires a non-empty list of values")
        placeholders = ", ".join(["?" for _ in value])
        return f"{column} IN ({placeholders})", list(value)

    if operator == "$like":
        if not isinstance(value, str):
            raise QueryExecutionError("$like value must be a string")
        return f"{column} LIKE ?", [value]

    operator_map = {
        "$eq": "=",
        "$ne": "!=",
        "$gt": ">",
        "$gte": ">=",
        "$lt": "<",
        "$lte": "<=",
    }
    sql_operator = operator_map.get(operator)
    if not sql_operator:
        raise QueryExecutionError(f"Unsupported operator '{operator}' for SQLite queries")
    return f"{column} {sql_operator} ?", [value]


def _build_order_by_clause(order_value: Any, allowed_columns: List[str]) -> str:
    if order_value in (None, [], ()):  # allow missing order_by
        return ""

    if not isinstance(order_value, (list, tuple)):
        raise QueryExecutionError("'order_by' must be a list of field/direction pairs")

    clauses: List[str] = []
    for entry in order_value:
        if isinstance(entry, dict) and len(entry) == 1:
            column, direction = next(iter(entry.items()))
        elif isinstance(entry, (list, tuple)) and len(entry) == 2:
            column, direction = entry
        else:
            raise QueryExecutionError("Invalid order_by entry; expected [field, direction]")

        if not isinstance(column, str) or column not in allowed_columns:
            raise QueryExecutionError(f"Column '{column}' is not available in SQLite table")

        dir_value = str(direction).lower() if direction is not None else "asc"
        direction_sql = "DESC" if dir_value in {"desc", "-1", "descending"} else "ASC"
        clauses.append(f"{column} {direction_sql}")

    return ", ".join(clauses)


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
