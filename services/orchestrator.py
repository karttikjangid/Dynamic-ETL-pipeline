"""Service-level orchestrators."""

from __future__ import annotations

import re
from typing import Optional, Tuple

from config import get_settings
from core import SchemaMetadata
from storage import schema_store
from storage.connection import MongoConnection
from utils.logger import get_logger


LOGGER = get_logger(__name__)
SETTINGS = get_settings()
_COLLECTION_SUFFIX = "records"


def _slugify_source(source_id: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", source_id.lower()).strip("_")
    return slug or "default"


def get_db_and_collection(source_id: str) -> Tuple[str, str]:
    """Return database and collection names for a source."""

    slug = _slugify_source(source_id)
    db_name = f"{SETTINGS.database_prefix}{slug}"
    collection_name = f"{slug}_{_COLLECTION_SUFFIX}"
    return db_name, collection_name


def handle_duplicate_upload(
    source_id: str,
    new_schema: SchemaMetadata,
    existing_schema: Optional[SchemaMetadata] = None,
) -> bool:
    """Determine if an upload represents the same schema as the latest version."""

    schema_to_compare = existing_schema
    if schema_to_compare is None:
        db_name, _ = get_db_and_collection(source_id)
        db = MongoConnection.get_instance().get_database(db_name)
        schema_to_compare = schema_store.retrieve_schema(db, source_id)

    if schema_to_compare is None:
        return False

    old_signature = _schema_signature(schema_to_compare)
    new_signature = _schema_signature(new_schema)

    is_duplicate = old_signature == new_signature
    if is_duplicate:
        LOGGER.info("Duplicate upload detected for source '%s'", source_id)
    return is_duplicate


def _schema_signature(schema: SchemaMetadata) -> Tuple[Tuple[str, str, bool], ...]:
    return tuple(
        sorted((field.name, field.type, field.nullable) for field in schema.fields)
    )
