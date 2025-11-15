"""MongoDB collection helpers."""

from __future__ import annotations

from typing import Dict, Iterable

from core import SchemaMetadata


def create_collection_from_schema(db, name: str, schema: SchemaMetadata) -> bool:
    """Create or update a collection to match the schema."""

    raise NotImplementedError


def build_mongo_validation_schema(schema: SchemaMetadata) -> Dict:
    """Build Mongo validation rules from SchemaMetadata."""

    raise NotImplementedError


def create_indexes(db, name: str, field_names: Iterable[str]):
    """Create indexes for frequently queried fields."""

    raise NotImplementedError


def alter_collection_add_field(db, name: str, field_name: str, field_type: str) -> bool:
    """Add a new field to an existing collection."""

    raise NotImplementedError
