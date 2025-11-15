"""API handlers bridging HTTP and services."""

from __future__ import annotations

import time
import uuid
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile
from threading import RLock
from typing import Any, Dict, Optional

from fastapi import HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from starlette import status

from core import (
    GetRecordsResponse,
    GetSchemaHistoryResponse,
    GetSchemaResponse,
    QueryResult,
    UploadResponse,
)
from core.exceptions import PipelineError, QueryExecutionError, SchemaInferenceError
from services.pipeline_service import process_upload
from services.query_service import execute_query
from services.schema_service import get_current_schema, get_schema_history
from utils.logger import get_logger

logger = get_logger(__name__)

READ_CHUNK_SIZE = 1024 * 512  # 512 KiB
QUERY_CACHE_TTL_SECONDS = 600
QUERY_CACHE_MAX_ENTRIES = 128


@dataclass
class CachedQueryResult:
    """Container for cached async query outputs."""

    source_id: str
    result: QueryResult
    expires_at: float


class QueryResultCache:
    """Simple in-memory cache for query results fetched asynchronously."""

    def __init__(self, ttl_seconds: int, max_entries: int):
        self.ttl_seconds = ttl_seconds
        self.max_entries = max_entries
        self._store: OrderedDict[str, CachedQueryResult] = OrderedDict()
        self._lock = RLock()

    def put(self, query_id: str, source_id: str, result: QueryResult) -> None:
        expires_at = time.time() + self.ttl_seconds
        with self._lock:
            self._store[query_id] = CachedQueryResult(source_id=source_id, result=result, expires_at=expires_at)
            self._store.move_to_end(query_id)
            if len(self._store) > self.max_entries:
                self._store.popitem(last=False)

    def get(self, query_id: str) -> Optional[CachedQueryResult]:
        with self._lock:
            cached = self._store.get(query_id)
            if not cached:
                return None
            if cached.expires_at < time.time():
                self._store.pop(query_id, None)
                return None
            self._store.move_to_end(query_id)
            return cached


QUERY_RESULT_CACHE = QueryResultCache(ttl_seconds=QUERY_CACHE_TTL_SECONDS, max_entries=QUERY_CACHE_MAX_ENTRIES)


async def handle_upload(file: UploadFile, source_id: Optional[str], version: Optional[int]) -> Dict[str, Any]:
    """Handle file uploads via the pipeline service."""

    resolved_source_id = source_id or _generate_source_id(file.filename)
    temp_path = await _persist_upload(file)

    try:
        upload_response: UploadResponse = await run_in_threadpool(process_upload, temp_path, resolved_source_id)
    except PipelineError as exc:  # pragma: no cover - domain-specific exceptions
        logger.exception("Upload processing failed for source %s", resolved_source_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
    finally:
        _cleanup_temp_file(temp_path)

    response = upload_response.dict()
    response["source_id"] = resolved_source_id
    if version is not None:
        response["requested_version"] = version
    return response


async def handle_get_schema(source_id: str) -> Dict[str, Any]:
    """Return the current schema metadata."""

    try:
        schema = await run_in_threadpool(get_current_schema, source_id)
    except SchemaInferenceError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PipelineError as exc:  # pragma: no cover
        logger.exception("Failed to fetch schema for %s", source_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc

    response = GetSchemaResponse(schema=schema, compatible_dbs=schema.compatible_dbs)
    return response.dict()


async def handle_get_schema_history(source_id: str) -> Dict[str, Any]:
    """Return schema history and diffs."""

    try:
        history = await run_in_threadpool(get_schema_history, source_id)
    except SchemaInferenceError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PipelineError as exc:  # pragma: no cover
        logger.exception("Failed to fetch schema history for %s", source_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc

    if not isinstance(history, GetSchemaHistoryResponse):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Schema history service returned an unexpected payload.",
        )

    return history.dict()


async def handle_get_records(source_id: str, limit: int, query_id: Optional[str]) -> Dict[str, Any]:
    """Return normalized records for the source."""

    if not query_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="query_id is required to fetch records.")

    cached = QUERY_RESULT_CACHE.get(query_id)
    if cached is None or cached.source_id != source_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Query results not found or expired.")

    limited_records = cached.result.results[:limit]
    response = GetRecordsResponse(count=len(limited_records), records=limited_records, source_id=source_id).dict()
    response.update({
        "query_id": query_id,
        "result_count": cached.result.result_count,
        "cached": True,
        "cache_expires_at": cached.expires_at,
    })
    return response


async def handle_query_execution(
    source_id: str, query: Dict[str, Any]
) -> Dict[str, Any]:
    """Execute strict query requests."""

    try:
        query_result: QueryResult = await run_in_threadpool(execute_query, source_id, query)
    except QueryExecutionError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except PipelineError as exc:  # pragma: no cover
        logger.exception("Query execution failed for %s", source_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc

    query_id = uuid.uuid4().hex
    QUERY_RESULT_CACHE.put(query_id, source_id, query_result)

    response = query_result.dict()
    response.update(
        {
            "query_id": query_id,
            "cached": True,
            "cache_ttl_seconds": QUERY_CACHE_TTL_SECONDS,
        }
    )
    return response


async def handle_health_check() -> Dict[str, Any]:
    """Return service health information."""

    return {
        "status": "ok",
        "timestamp": time.time(),
        "services": {
            "pipeline": "ready",
            "storage": "ready",
        },
    }


async def _persist_upload(file: UploadFile) -> str:
    """Stream an UploadFile to a temp file and return its path."""

    suffix = Path(file.filename or "payload.txt").suffix or ".txt"
    with NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
        while True:
            chunk = await file.read(READ_CHUNK_SIZE)
            if not chunk:
                break
            tmp_file.write(chunk)
        temp_path = tmp_file.name

    await file.close()
    return temp_path


def _cleanup_temp_file(path: str) -> None:
    """Delete a temp file if it exists."""

    try:
        Path(path).unlink(missing_ok=True)
    except OSError:  # pragma: no cover - best effort cleanup
        logger.warning("Failed to delete temp file %s", path)


def _generate_source_id(filename: Optional[str]) -> str:
    """Generate a deterministic-leaning fallback source identifier."""

    safe_stem = Path(filename or "source").stem or "source"
    sanitized = "".join(ch for ch in safe_stem if ch.isalnum() or ch in {"_", "-"})
    sanitized = sanitized.lower().strip("-") or "source"
    return f"{sanitized}-{uuid.uuid4().hex[:8]}"

