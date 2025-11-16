"""Pipeline service orchestrating extraction → normalization → storage."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from core import NormalizedRecord, SchemaMetadata, TabularSchemaGroup, UploadResponse
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
from services.ner_service import apply_ner_to_fragments
from storage import collection_manager, document_inserter, schema_store
from storage.connection import MongoConnection
from storage.sqlite_connection import SQLiteConnection
from storage.sqlite_table_manager import create_table_from_schema
from storage.sqlite_document_inserter import batch_insert_documents_sqlite
from storage.storage_router import categorize_records_by_storage, get_compatible_dbs_for_schema
from storage.sqlite_db_locator import get_version_db_path
from services.schema_grouping_service import group_tabular_documents
from utils.logger import get_logger


LOGGER = get_logger(__name__)


def process_upload(file_path: str, source_id: str, enable_ner: bool = True) -> UploadResponse:
    """Process a newly uploaded file and return upload metadata.

    Args:
        file_path: Path to the file to process
        source_id: Identifier for the data source
        enable_ner: Whether to apply Named Entity Recognition (default: True)
    """

    resolved_path = Path(file_path).expanduser().resolve()
    if not resolved_path.is_file():
        raise ExtractionError(f"File not found: {file_path}")

    file_id = uuid4().hex
    db_name = get_database_name(source_id)
    collection_name = get_collection_name(source_id)
    mongo_connection = MongoConnection.get_instance()
    db = mongo_connection.get_database(db_name)
    sqlite_connection = SQLiteConnection.get_instance()

    # Evidence tracking for Tier-B
    evidence = {}

    try:
        extracted_records, fragment_stats = extract_all_records(str(resolved_path))
        evidence["extraction"] = {
            "status": "success",
            "fragments": fragment_stats,
            "total_records": len(extracted_records)
        }
    except Exception as exc:  # pragma: no cover - extractor errors bubbled
        LOGGER.exception("Extraction failed for '%s': %s", file_path, exc)
        evidence["extraction"] = {"status": "failed", "error": str(exc)}
        raise ExtractionError("Unable to extract records") from exc

    records_extracted = len(extracted_records)
    if records_extracted == 0:
        evidence["extraction"]["status"] = "empty"
        return UploadResponse(
            status="empty",
            source_id=source_id,
            file_id=file_id,
            schema_id="",
            version=0,
            records_extracted=0,
            records_normalized=0,
            parsed_fragments_summary=fragment_stats,
            evidence=evidence
        )

    extracted_payloads: List[Dict[str, Any]] = [record.model_dump() for record in extracted_records]

    try:
        normalized_records = normalize_all_records(extracted_payloads)
        evidence["normalization"] = {
            "status": "success",
            "records_normalized": len(normalized_records)
        }
    except Exception as exc:  # pragma: no cover - normalization errors bubbled
        LOGGER.exception("Normalization failed for source '%s': %s", source_id, exc)
        evidence["normalization"] = {"status": "failed", "error": str(exc)}
        raise NormalizationError("Unable to normalize records") from exc

    if not normalized_records:
        raise NormalizationError("No records produced after normalization")

    # Categorize records by storage type (MongoDB vs SQLite)
    categorized = categorize_records_by_storage(normalized_records)
    mongodb_records = categorized["mongodb"]
    sqlite_records = categorized["sqlite"]

    evidence["storage_routing"] = {
        "mongodb_records": len(mongodb_records),
        "sqlite_records": len(sqlite_records)
    }

    # Apply NER if enabled (after normalization, before storage)
    normalized_docs = _serialize_normalized_records(normalized_records)
    if enable_ner:
        try:
            normalized_docs = apply_ner_to_fragments(normalized_docs)
            LOGGER.info("NER applied to %d fragments for source '%s'", len(normalized_docs), source_id)
            evidence["ner"] = {"status": "success", "fragments_enriched": len(normalized_docs)}
        except Exception as exc:
            # Log NER failure but don't block the pipeline
            LOGGER.warning("NER processing failed for source '%s': %s", source_id, exc)
            evidence["ner"] = {"status": "failed", "error": str(exc)}

    # Keep NormalizedRecord instances in sync with enriched docs
    for idx, record in enumerate(normalized_records):
        record.data = normalized_docs[idx]

    records_normalized = len(normalized_docs)

    if records_normalized == 0:
        raise NormalizationError("Normalized payloads are empty")

    existing_schema = None
    sqlite_schema: Optional[SchemaMetadata] = None
    try:
        existing_schema = schema_service.get_current_schema(source_id)
    except SchemaInferenceError:
        existing_schema = None

    try:
        new_schema = schema_service.compute_schema_for_source(normalized_records, source_id)
        if sqlite_records:
            sqlite_schema = schema_service.compute_schema_for_source(sqlite_records, source_id)
        # Update compatible databases based on schema shape
        compatible_dbs = get_compatible_dbs_for_schema(new_schema, sqlite_schema)
        new_schema.compatible_dbs = compatible_dbs
        evidence["schema_inference"] = {
            "status": "success",
            "fields_detected": len(new_schema.fields),
            "compatible_dbs": compatible_dbs
        }
        if sqlite_schema:
            evidence["schema_inference"]["sqlite_fields"] = len(sqlite_schema.fields)
    except Exception as exc:  # pragma: no cover
        LOGGER.exception("Schema inference failed for source '%s': %s", source_id, exc)
        evidence["schema_inference"] = {"status": "failed", "error": str(exc)}
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

    # Storage preparation and insertion
    mongodb_inserted = 0
    sqlite_inserted = 0

    # MongoDB storage (for JSON/YAML)
    if mongodb_records:
        if not duplicate_upload:
            collection_created = collection_manager.create_collection_from_schema(
                db, collection_name, prepared_schema
            )
            if not collection_created:
                raise StorageError("Failed to prepare MongoDB collection")

        mongodb_docs = _serialize_normalized_records(mongodb_records)
        valid_docs = _filter_valid_documents(mongodb_docs, active_schema)
        mongodb_inserted = document_inserter.batch_insert_documents(
            db, collection_name, valid_docs, batch_size=DEFAULT_BATCH_SIZE
        )
        LOGGER.info(f"Inserted {mongodb_inserted} records into MongoDB")

    tabular_groups: List[TabularSchemaGroup] = []

    # SQLite storage (for CSV/HTML/KV)
    if sqlite_records:
        db_path = get_version_db_path(source_id, target_version)
        sqlite_docs = _serialize_normalized_records(sqlite_records)
        group_plans = group_tabular_documents(sqlite_docs, source_id, target_version)

        for plan in group_plans:
            tabular_groups.append(plan.group)
            if not duplicate_upload:
                table_created = create_table_from_schema(
                    sqlite_connection,
                    db_path,
                    plan.group.table_name,
                    plan.group.fields,
                )
                if not table_created:
                    raise StorageError(f"Failed to prepare SQLite table '{plan.group.table_name}'")

            inserted_count = batch_insert_documents_sqlite(
                sqlite_connection,
                db_path,
                plan.group.table_name,
                plan.documents,
                source_id,
            )
            sqlite_inserted += inserted_count
            LOGGER.info(
                "Inserted %d records into SQLite table '%s' (db=%s)",
                inserted_count,
                plan.group.table_name,
                db_path,
            )

        if tabular_groups:
            if "sqlite" not in prepared_schema.compatible_dbs:
                prepared_schema.compatible_dbs.append("sqlite")
            prepared_schema.tabular_groups = tabular_groups

    inserted = mongodb_inserted + sqlite_inserted
    storage_summary: Dict[str, Any] = {
        "mongodb_inserted": mongodb_inserted,
        "sqlite_inserted": sqlite_inserted,
        "total_inserted": inserted,
    }
    if tabular_groups:
        storage_summary["sqlite_tables"] = [group.table_name for group in tabular_groups]
    evidence["storage"] = storage_summary

    if inserted == 0:
        LOGGER.warning("No documents inserted for source '%s'", source_id)

    should_persist_schema = (not duplicate_upload) or (tabular_groups != [])
    if should_persist_schema:
        if not schema_store.store_schema(db, prepared_schema):
            raise StorageError("Failed to persist schema metadata")

    status = "success" if inserted > 0 else "noop"
    response_schema_id = active_schema.schema_id if active_schema else schema_id

    return UploadResponse(
        status=status,
        source_id=source_id,
        file_id=file_id,
        schema_id=response_schema_id,
        version=target_version,
        records_extracted=records_extracted,
        records_normalized=inserted,
        parsed_fragments_summary=fragment_stats,
        evidence=evidence,
        schema_metadata=prepared_schema
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
