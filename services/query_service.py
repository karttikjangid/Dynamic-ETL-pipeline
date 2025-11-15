"""Strict query execution service."""

from __future__ import annotations

from typing import Any, Dict

from core import QueryResult


def execute_query(source_id: str, query: Dict[str, Any]) -> QueryResult:
    """Execute a strict Mongo/SQL-style query and return results."""

    raise NotImplementedError
