"""Document insertion helpers."""

from __future__ import annotations

from typing import Dict, List

from pymongo.errors import PyMongoError

from core import SchemaMetadata
from utils.logger import get_logger


_LOGGER = get_logger(__name__)


def _is_valid_type(value, expected: str) -> bool:
    if value is None:
        return True

    expected = (expected or "").lower()

    if expected in {"int", "integer"}:
        return isinstance(value, int) and not isinstance(value, bool)
    if expected in {"float", "double", "number"}:
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected in {"bool", "boolean"}:
        return isinstance(value, bool)
    if expected in {"datetime"}:
        from datetime import datetime

        return isinstance(value, datetime) or (
            isinstance(value, str) and value.endswith("Z")
        )
    if expected in {"object"}:
        return isinstance(value, dict)
    if expected in {"array"}:
        return isinstance(value, list)
    return isinstance(value, str)


def insert_documents(db, name: str, docs: List[Dict]) -> int:
    """Insert documents sequentially."""

    if not docs:
        return 0

    collection = db[name]
    inserted = 0
    for doc in docs:
        try:
            collection.insert_one(doc)
            inserted += 1
        except PyMongoError as exc:
            _LOGGER.error("Failed to insert document into '%s': %s", name, exc)
    return inserted


def batch_insert_documents(
    db, name: str, docs: List[Dict], batch_size: int = 100
) -> int:
    """Insert documents in batches for efficiency."""

    if not docs:
        return 0

    if batch_size <= 0:
        batch_size = 100

    collection = db[name]
    total_inserted = 0
    for start in range(0, len(docs), batch_size):
        chunk = docs[start : start + batch_size]
        try:
            result = collection.insert_many(chunk, ordered=False)
            total_inserted += len(result.inserted_ids)
        except PyMongoError as exc:
            _LOGGER.error(
                "Failed to insert batch into '%s' (size=%d): %s",
                name,
                len(chunk),
                exc,
            )
    return total_inserted


def validate_document_for_insertion(doc: Dict, schema: SchemaMetadata) -> bool:
    """Ensure documents comply with schema prior to insertion."""

    if not isinstance(doc, dict):
        return False

    schema_fields = {field.name: field for field in schema.fields}
    for key, value in doc.items():
        if key == "_id":
            continue
        field = schema_fields.get(key)
        if field is None:
            _LOGGER.warning("Document contains unknown field '%s'", key)
            return False
        if not _is_valid_type(value, field.type):
            _LOGGER.warning("Field '%s' failed type validation (expected %s)", key, field.type)
            return False
    return True
