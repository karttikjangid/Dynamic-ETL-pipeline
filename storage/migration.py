"""Schema migration helpers."""

from __future__ import annotations

from typing import Dict, List

from core import SchemaDiff, SchemaMetadata


def detect_schema_change(old: SchemaMetadata, new: SchemaMetadata) -> SchemaDiff:
    """Compare schemas and produce a diff."""

    raise NotImplementedError


def find_added_fields(old_fields: List[str], new_fields: List[str]) -> List[str]:
    """Return newly added fields."""

    raise NotImplementedError


def find_removed_fields(old_fields: List[str], new_fields: List[str]) -> List[str]:
    """Return removed fields."""

    raise NotImplementedError


def find_type_changes(old_schema: SchemaMetadata, new_schema: SchemaMetadata) -> Dict[str, Dict[str, str]]:
    """Return changed field types."""

    raise NotImplementedError


def evolve_collection_schema(db, name: str, old_schema: SchemaMetadata, new_schema: SchemaMetadata) -> bool:
    """Apply schema evolution operations."""

    raise NotImplementedError
