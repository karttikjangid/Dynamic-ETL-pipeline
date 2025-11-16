"""Pydantic models shared across the pipeline."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel


class ExtractedRecord(BaseModel):
    """Single record extracted from source files."""

    data: Union[Dict[str, Any], List[Dict[str, Any]]]  # Dict for single records, List[Dict] for tables/CSV
    source_type: str  # "json", "kv", "html_table", "csv_block", "yaml_block"
    confidence: float = 1.0
    metadata: Optional[Dict[str, Any]] = None  # Tier-B: offsets, fragment_id, etc.


class NormalizedRecord(BaseModel):
    """Record produced by normalization orchestrators."""

    data: Dict[str, Any]
    source_type: str
    extraction_confidence: float
    provenance: Optional[Dict[str, Any]] = None  # Tier-B: fragment tracking


class SchemaField(BaseModel):
    """Definition for a single field in the inferred schema."""

    name: str
    path: Optional[str] = None  # Tier-B: nested path like "pricing.price_usd"
    type: str
    nullable: bool = True
    example_value: Optional[Any] = None
    confidence: float = 1.0
    source_offsets: Optional[List[int]] = None  # Tier-B: where field appears
    suggested_index: bool = False  # Tier-B: hint for SQLite indexes
    source_path: Optional[str] = None  # Legacy support


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
    primary_key_candidates: Optional[List[str]] = None  # Tier-B
    migration_notes: Optional[str] = None  # Tier-B
    version_diff: Optional[Dict[str, Any]] = None  # Tier-B: DeepDiff output
    genson_schema: Optional[Dict[str, Any]] = None  # Tier-B: raw Genson schema


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
    version: int  # Tier-B
    records_extracted: int
    records_normalized: int
    parsed_fragments_summary: Dict[str, int]
    evidence: Optional[Dict[str, Any]] = None  # Tier-B: phase-by-phase evidence
    schema_metadata: Optional[SchemaMetadata] = None  # Tier-B: full schema in response


class GetSchemaResponse(BaseModel):
    """Response for current schema retrieval."""

    schema_data: SchemaMetadata
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
