"""Schema service helpers."""

from __future__ import annotations

from core import GetSchemaHistoryResponse, SchemaMetadata


def get_current_schema(source_id: str) -> SchemaMetadata:
    """Return the latest schema for a source."""

    raise NotImplementedError


def get_schema_history(source_id: str) -> GetSchemaHistoryResponse:
    """Return all schema versions plus diffs."""

    raise NotImplementedError


def handle_schema_evolution(source_id: str, old_schema: SchemaMetadata, new_schema: SchemaMetadata) -> bool:
    """Apply schema evolution procedures when needed."""

    raise NotImplementedError
