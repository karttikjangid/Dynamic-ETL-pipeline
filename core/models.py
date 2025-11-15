"""Pydantic models shared across the pipeline."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel


class ExtractedRecord(BaseModel):
    """Single record extracted from source files."""

    data: Dict[str, Any]
    source_type: str  # "json" or "kv"
    confidence: float = 1.0


class NormalizedRecord(BaseModel):
    """Record produced by normalization orchestrators."""

    data: Dict[str, Any]
    original_source: str
    extraction_confidence: float


class SchemaField(BaseModel):
    """Definition for a single field in the inferred schema."""

    name: str
    type: str
    nullable: bool = True
    example_value: Optional[Any] = None
    confidence: float = 1.0
    source_path: Optional[str] = None


class SchemaMetadata(BaseModel):
    """Schema output persisted alongside ingested records."""

    schema_id: str
    source_id: str
    version: int
    fields: List[SchemaField]
    generated_at: datetime
    compatible_dbs: List[str] = ["mongodb"]
    record_count: int
    extraction_stats: Dict[str, Union[int, float]]


class SchemaDiff(BaseModel):
    """Minimal diff representation between schema versions."""

    added_fields: List[str]
    removed_fields: List[str]
    type_changes: Dict[str, Dict[str, str]]
    migration_notes: str


class UploadResponse(BaseModel):
    """Response payload returned after file uploads."""

    status: str
    source_id: str
    file_id: str
    schema_id: str
    records_extracted: int
    records_normalized: int
    parsed_fragments_summary: Dict[str, int]


class GetSchemaResponse(BaseModel):
    """Response for current schema retrieval."""

    schema: SchemaMetadata
    compatible_dbs: List[str]


class GetSchemaHistoryResponse(BaseModel):
    """Response for schema history requests."""

    schemas: List[SchemaMetadata]
    diffs: List[SchemaDiff]


class GetRecordsResponse(BaseModel):
    """Response for record retrieval requests."""

    count: int
    records: List[Dict[str, Any]]
    source_id: str


class QueryResult(BaseModel):
    """Query execution result metadata."""

    query: Dict[str, Any]
    results: List[Dict[str, Any]]
    result_count: int
    execution_time_ms: float
