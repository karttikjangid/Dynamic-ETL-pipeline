"""Shared constants for the Dynamic ETL Pipeline."""

SUPPORTED_SOURCE_TYPES = ("json", "kv")
DEFAULT_CONFIDENCE = 1.0
SCHEMA_ID_TEMPLATE = "{source_id}_v{version}"
DEFAULT_BATCH_SIZE = 100
MAX_SCHEMA_FIELDS = 500
MONGODB_COMPATIBLE_DBS = ["mongodb"]
