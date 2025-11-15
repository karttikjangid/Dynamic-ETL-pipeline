"""Tier A test coverage for the Dynamic ETL pipeline."""

from __future__ import annotations

from uuid import uuid4

import pytest

from services.pipeline_service import process_upload
from services import query_service, schema_service
from tests.payloads import TEST_PAYLOADS


def _write_payload(tmp_path, content: str, suffix: str = ".txt") -> str:
    file_path = tmp_path / f"tier_a_{uuid4().hex}{suffix}"
    file_path.write_text(content)
    return str(file_path)


@pytest.mark.integration
def test_tier_a01_kv_and_json_fragments(tmp_path):
    source_id = "tier-a-01"
    file_path = _write_payload(tmp_path, TEST_PAYLOADS["tier_a_01_kv_and_json"])

    response = process_upload(file_path, source_id)

    assert response.status == "success"
    assert response.parsed_fragments_summary["json_fragments"] >= 1
    assert response.parsed_fragments_summary["kv_pairs"] >= 1

    schema = schema_service.get_current_schema(source_id)
    field_names = {field.name for field in schema.fields}
    assert {"transaction_id", "amount", "owner", "summary"}.issubset(field_names)

    query = query_service.execute_query(source_id, {"filter": {"transaction_id": "A01-TXN-001"}})
    assert query.result_count == 1
    assert query.results[0]["currency"] == "USD"


@pytest.mark.integration
def test_tier_a02_markdown_code_block(tmp_path):
    source_id = "tier-a-02"
    file_path = _write_payload(
        tmp_path,
        TEST_PAYLOADS["tier_a_02_markdown_code_block"],
        suffix=".md",
    )

    response = process_upload(file_path, source_id)

    assert response.status == "success"
    assert response.parsed_fragments_summary["json_fragments"] >= 1

    schema = schema_service.get_current_schema(source_id)
    field_names = {field.name for field in schema.fields}
    assert {"user_id", "username", "status"}.issubset(field_names)

    query = query_service.execute_query(source_id, {"filter": {"user_id": 8888}})
    assert query.result_count == 1
    assert query.results[0]["username"] == "tier_a_code"


@pytest.mark.integration
def test_tier_a03_csv_like_text(tmp_path):
    source_id = "tier-a-03"
    file_path = _write_payload(tmp_path, TEST_PAYLOADS["tier_a_03_csv_like_text"])

    response = process_upload(file_path, source_id)

    assert response.status == "success"
    assert response.records_extracted >= 1

    schema = schema_service.get_current_schema(source_id)
    field_names = {field.name for field in schema.fields}
    assert "csv_metadata" in field_names

    query = query_service.execute_query(
        source_id,
        {"filter": {"csv_metadata.records": 3}},
    )
    assert query.result_count == 1


@pytest.mark.integration
def test_tier_a04_html_snippet(tmp_path):
    source_id = "tier-a-04"
    file_path = _write_payload(tmp_path, TEST_PAYLOADS["tier_a_04_html_snippet"])

    response = process_upload(file_path, source_id)

    assert response.status == "success"
    assert response.records_extracted >= 1

    schema = schema_service.get_current_schema(source_id)
    field_names = {field.name for field in schema.fields}
    assert {"table_summary", "html_hint"}.issubset(field_names)

    query = query_service.execute_query(
        source_id,
        {"filter": {"table_summary.rows": 2}},
    )
    assert query.result_count == 1


@pytest.mark.integration
def test_tier_a05_pdf_like_text(tmp_path):
    source_id = "tier-a-05"
    file_path = _write_payload(tmp_path, TEST_PAYLOADS["tier_a_05_pdf_like_text"])

    response = process_upload(file_path, source_id)

    assert response.status == "success"
    assert response.records_extracted >= 1

    schema = schema_service.get_current_schema(source_id)
    field_names = {field.name for field in schema.fields}
    assert {"document_type", "extracted_by"}.issubset(field_names)

    query = query_service.execute_query(source_id, {"filter": {"document_type": "pdf"}})
    assert query.result_count == 1


@pytest.mark.integration
def test_tier_a06_duplicate_upload_idempotent(tmp_path):
    source_id = "tier-a-06"
    file_path = _write_payload(tmp_path, TEST_PAYLOADS["tier_a_01_kv_and_json"])

    first = process_upload(file_path, source_id)
    second = process_upload(file_path, source_id)

    assert first.schema_id == second.schema_id

    history = schema_service.get_schema_history(source_id)
    assert len(history.schemas) == 1


@pytest.mark.integration
def test_tier_a07_whitespace_variation_no_schema_churn(tmp_path):
    source_id = "tier-a-07"
    base_content = TEST_PAYLOADS["tier_a_01_kv_and_json"]
    variant_content = "\n".join(f"  {line}  " for line in base_content.splitlines())

    base_path = _write_payload(tmp_path, base_content)
    variant_path = _write_payload(tmp_path, variant_content)

    first = process_upload(base_path, source_id)
    second = process_upload(variant_path, source_id)

    assert first.schema_id == second.schema_id


@pytest.mark.integration
def test_tier_a08_malformed_json_surfaces_error(tmp_path):
    source_id = "tier-a-08"
    file_path = _write_payload(tmp_path, TEST_PAYLOADS["tier_a_08_malformed_json"])

    response = process_upload(file_path, source_id)

    assert response.status == "success"
    assert response.parsed_fragments_summary["json_fragments"] >= 1

    query = query_service.execute_query(source_id, {"filter": {"_parse_error": True}})
    assert query.result_count >= 1