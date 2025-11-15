"""API handlers bridging HTTP and services."""

from __future__ import annotations

from typing import Any, Dict


async def handle_upload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Handle file uploads via the pipeline service."""

    raise NotImplementedError


async def handle_get_schema(source_id: str) -> Dict[str, Any]:
    """Return the current schema metadata."""

    raise NotImplementedError


async def handle_get_schema_history(source_id: str) -> Dict[str, Any]:
    """Return schema history and diffs."""

    raise NotImplementedError


async def handle_get_records(source_id: str, limit: int) -> Dict[str, Any]:
    """Return normalized records for the source."""

    raise NotImplementedError


async def handle_query_execution(
    source_id: str, query: Dict[str, Any]
) -> Dict[str, Any]:
    """Execute strict query requests."""

    raise NotImplementedError


async def handle_health_check() -> Dict[str, Any]:
    """Return service health information."""

    raise NotImplementedError
