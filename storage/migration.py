"""Schema migration helpers."""

from __future__ import annotations

from typing import Dict, List

from pymongo.errors import PyMongoError

from core import SchemaDiff, SchemaMetadata
from utils.logger import get_logger


_LOGGER = get_logger(__name__)


def detect_schema_change(old: SchemaMetadata, new: SchemaMetadata) -> SchemaDiff:
    """Compare schemas and produce a diff."""

    old_fields = {field.name: field for field in old.fields}
    new_fields = {field.name: field for field in new.fields}

    added = find_added_fields(list(old_fields.keys()), list(new_fields.keys()))
    removed = find_removed_fields(list(old_fields.keys()), list(new_fields.keys()))
    type_changes = find_type_changes(old, new)

    notes: List[str] = []
    if added:
        notes.append(f"Added: {', '.join(added)}")
    if removed:
        notes.append(f"Removed: {', '.join(removed)}")
    if type_changes:
        notes.append("Type changes present")

    return SchemaDiff(
        added_fields=added,
        removed_fields=removed,
        type_changes=type_changes,
        migration_notes="; ".join(notes) if notes else "No changes",
    )


def find_added_fields(old_fields: List[str], new_fields: List[str]) -> List[str]:
    """Return newly added fields."""

    return sorted(set(new_fields) - set(old_fields))


def find_removed_fields(old_fields: List[str], new_fields: List[str]) -> List[str]:
    """Return removed fields."""

    return sorted(set(old_fields) - set(new_fields))


def find_type_changes(
    old_schema: SchemaMetadata, new_schema: SchemaMetadata
) -> Dict[str, Dict[str, str]]:
    """Return changed field types."""

    changes: Dict[str, Dict[str, str]] = {}
    old_map = {field.name: field.type for field in old_schema.fields}
    for field in new_schema.fields:
        old_type = old_map.get(field.name)
        if old_type and old_type != field.type:
            changes[field.name] = {"old": old_type, "new": field.type}
    return changes


def evolve_collection_schema(
    db, name: str, old_schema: SchemaMetadata, new_schema: SchemaMetadata
) -> bool:
    """Apply schema evolution operations."""

    diff = detect_schema_change(old_schema, new_schema)
    if not diff.added_fields and not diff.type_changes:
        return True

    collection = db[name]

    try:
        for field_name in diff.added_fields:
            collection.update_many({field_name: {"$exists": False}}, {"$set": {field_name: None}})

        for field_name, change in diff.type_changes.items():
            # Basic strategy: coerce incompatible types by moving values to a fallback field
            fallback_field = f"{field_name}_legacy"
            collection.update_many(
                {
                    field_name: {
                        "$type": "string" if change["old"] == "string" else "missing",
                    }
                },
                {
                    "$set": {fallback_field: f"type-migrated from {change['old']}"},
                },
            )
        return True
    except PyMongoError as exc:
        _LOGGER.error("Failed to evolve collection '%s': %s", name, exc)
        return False
