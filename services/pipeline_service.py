"""Pipeline service orchestrating extraction → normalization → storage."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from core import NormalizedRecord, SchemaMetadata, UploadResponse
from core.constants import DEFAULT_BATCH_SIZE, SCHEMA_ID_TEMPLATE
from core.exceptions import (
    ExtractionError,
    NormalizationError,
    SchemaInferenceError,
    StorageError,
)
from extractors.orchestrator import extract_all_records
from normalizers.orchestrator import normalize_all_records
from services import orchestrator as service_orchestrator
from services import schema_service
from storage import collection_manager, document_inserter, schema_store
from storage.connection import MongoConnection
from utils.logger import get_logger


LOGGER = get_logger(__name__)


def process_upload(file_path: str, source_id: str) -> UploadResponse:
    """Process a newly uploaded file and return upload metadata."""

    resolved_path = Path(file_path).expanduser().resolve()
    if not resolved_path.is_file():
        raise ExtractionError(f"File not found: {file_path}")

    file_id = uuid4().hex
    db_name = get_database_name(source_id)
    collection_name = get_collection_name(source_id)
    connection = MongoConnection.get_instance()
    db = connection.get_database(db_name)

    try:
        extracted_records, fragment_stats = extract_all_records(str(resolved_path))
    except Exception as exc:  # pragma: no cover - extractor errors bubbled
        LOGGER.exception("Extraction failed for '%s': %s", file_path, exc)
        raise ExtractionError("Unable to extract records") from exc

    records_extracted = len(extracted_records)
    if records_extracted == 0:
        return UploadResponse(
            status="empty",
            source_id=source_id,
            file_id=file_id,
            schema_id="",
            records_extracted=0,
            records_normalized=0,
            parsed_fragments_summary=fragment_stats,
        )

    extracted_payloads: List[Dict[str, Any]] = [record.dict() for record in extracted_records]

    try:
        normalized_records = normalize_all_records(extracted_payloads)
    except Exception as exc:  # pragma: no cover - normalization errors bubbled
        LOGGER.exception("Normalization failed for source '%s': %s", source_id, exc)
        raise NormalizationError("Unable to normalize records") from exc

    if not normalized_records:
        raise NormalizationError("No records produced after normalization")

    normalized_docs = _serialize_normalized_records(normalized_records)
    records_normalized = len(normalized_docs)

    if records_normalized == 0:
        raise NormalizationError("Normalized payloads are empty")

    existing_schema = None
    try:
        existing_schema = schema_service.get_current_schema(source_id)
    except SchemaInferenceError:
        existing_schema = None

    try:
        new_schema = schema_service.compute_schema_for_source(normalized_records, source_id)
    except Exception as exc:  # pragma: no cover
        LOGGER.exception("Schema inference failed for source '%s': %s", source_id, exc)
        raise SchemaInferenceError("Schema generation failed") from exc

    target_version = 1
    duplicate_upload = False
    if existing_schema is not None:
        duplicate_upload = service_orchestrator.handle_duplicate_upload(
            source_id, new_schema, existing_schema
        )
        target_version = existing_schema.version if duplicate_upload else existing_schema.version + 1

    schema_id = SCHEMA_ID_TEMPLATE.format(source_id=source_id, version=target_version)
    combined_stats = {**new_schema.extraction_stats, **fragment_stats}
    prepared_schema = new_schema.model_copy(
        update={
            "version": target_version,
            "schema_id": schema_id,
            "extraction_stats": combined_stats,
        }
    )
    active_schema = existing_schema if duplicate_upload and existing_schema else prepared_schema

    if existing_schema and not duplicate_upload:
        schema_service.handle_schema_evolution(source_id, existing_schema, prepared_schema)

    if not duplicate_upload:
        collection_created = collection_manager.create_collection_from_schema(
            db, collection_name, prepared_schema
        )
        if not collection_created:
            raise StorageError("Failed to prepare MongoDB collection")

    valid_docs = _filter_valid_documents(normalized_docs, active_schema)
    inserted = document_inserter.batch_insert_documents(
        db, collection_name, valid_docs, batch_size=DEFAULT_BATCH_SIZE
    )

    if inserted == 0:
        LOGGER.warning("No documents inserted for source '%s'", source_id)

    if not duplicate_upload:
        if not schema_store.store_schema(db, prepared_schema):
            raise StorageError("Failed to persist schema metadata")

    status = "success" if inserted > 0 else "noop"
    response_schema_id = active_schema.schema_id if active_schema else schema_id

    return UploadResponse(
        status=status,
        source_id=source_id,
        file_id=file_id,
        schema_id=response_schema_id,
        records_extracted=records_extracted,
        records_normalized=inserted,
        parsed_fragments_summary=fragment_stats,
    )


def get_database_name(source_id: str) -> str:
    """Return deterministic database name for a source."""

    db_name, _ = service_orchestrator.get_db_and_collection(source_id)
    return db_name


def get_collection_name(source_id: str) -> str:
    """Return deterministic collection name for a source."""

    _, collection_name = service_orchestrator.get_db_and_collection(source_id)
    return collection_name


def _serialize_normalized_records(records: List[NormalizedRecord]) -> List[Dict[str, Any]]:
    serialized: List[Dict[str, Any]] = []
    for record in records:
        serialized.append(dict(record.data))
    return serialized


def _filter_valid_documents(
    docs: List[Dict[str, Any]], schema: Optional[SchemaMetadata]
) -> List[Dict[str, Any]]:
    if schema is None:
        return docs
    valid = []
    for doc in docs:
        if document_inserter.validate_document_for_insertion(doc, schema):
            valid.append(doc)
    return valid
