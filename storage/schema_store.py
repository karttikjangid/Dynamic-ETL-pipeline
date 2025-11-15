"""Schema persistence helpers."""

from __future__ import annotations

from typing import List, Optional

from core import SchemaMetadata


def store_schema(db, schema: SchemaMetadata) -> bool:
    """Persist schema metadata to the schema collection."""

    raise NotImplementedError


def retrieve_schema(
    db, source_id: str, version: Optional[int] = None
) -> Optional[SchemaMetadata]:
    """Fetch a schema by source id and optional version."""

    raise NotImplementedError


def get_schema_history(db, source_id: str) -> List[SchemaMetadata]:
    """Return all versions for a source."""

    raise NotImplementedError


def get_latest_schema_version(db, source_id: str) -> int:
    """Return the latest schema version for a source id."""

    raise NotImplementedError
