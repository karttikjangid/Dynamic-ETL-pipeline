"""MongoDB collection helpers."""

from __future__ import annotations

from typing import Dict, Iterable

from pymongo.errors import PyMongoError

from core import SchemaMetadata
from utils.logger import get_logger


_LOGGER = get_logger(__name__)


_TYPE_MAPPING = {
    "string": "string",
    "int": "int",
    "integer": "int",
    "float": "double",
    "double": "double",
    "number": "double",
    "bool": "bool",
    "boolean": "bool",
    "datetime": "date",
    "object": "object",
    "array": "array",
}


def _map_schema_type(field_type: str) -> str:
    return _TYPE_MAPPING.get(field_type.lower(), "string") if field_type else "string"


def create_collection_from_schema(db, name: str, schema: SchemaMetadata) -> bool:
    """Create or update a collection to match the schema."""

    validator = build_mongo_validation_schema(schema)
    try:
        # Ensure collection exists with the expected validator.
        if name not in db.list_collection_names():
            db.create_collection(name, validator=validator)
        else:
            db.command("collMod", name, validator=validator)

        field_names = [field.name for field in schema.fields]
        create_indexes(db, name, field_names)
        return True
    except PyMongoError as exc:
        _LOGGER.error("Failed to sync collection '%s': %s", name, exc)
        return False


def build_mongo_validation_schema(schema: SchemaMetadata) -> Dict:
    """Build Mongo validation rules from SchemaMetadata."""

    properties = {}
    for field in schema.fields:
        bson_type = _map_schema_type(field.type)
        properties[field.name] = {"bsonType": bson_type}
        if field.example_value is not None:
            properties[field.name]["description"] = f"example: {field.example_value}"

    # Allow optional fields but still validate known ones when present.
    return {
        "$jsonSchema": {
            "bsonType": "object",
            "properties": properties,
            "additionalProperties": True,
        }
    }


def create_indexes(db, name: str, field_names: Iterable[str]):
    """Create indexes for frequently queried fields."""

    collection = db[name]
    for field_name in field_names:
        if not field_name or field_name == "_id":
            continue
        try:
            collection.create_index([(field_name, 1)], background=True)
        except PyMongoError as exc:
            _LOGGER.warning("Skipping index on '%s.%s': %s", name, field_name, exc)


def alter_collection_add_field(db, name: str, field_name: str, field_type: str) -> bool:
    """Add a new field to an existing collection."""

    collection = db[name]
    try:
        # Ensure existing documents have the field so reads stay consistent.
        collection.update_many({field_name: {"$exists": False}}, {"$set": {field_name: None}})
        return True
    except PyMongoError as exc:
        _LOGGER.error("Failed to add field '%s' to '%s': %s", field_name, name, exc)
        return False
