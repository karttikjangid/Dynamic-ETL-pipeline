"""End-to-end service tests using a mongomock-backed MongoDB."""

from __future__ import annotations

import pytest

from services.pipeline_service import process_upload
from services import query_service, schema_service
from tests.payloads import TEST_PAYLOADS


@pytest.mark.integration
def test_process_upload_and_query_roundtrip(tmp_path):
    """Upload a sample file and ensure queries return expected records."""

    source_id = "demo-source"
    file_content = TEST_PAYLOADS["test_case_7_mixed_json_and_kv_same_file"]

    sample_file = tmp_path / "sample_input.txt"
    sample_file.write_text(file_content)

    response = process_upload(str(sample_file), source_id)

    assert response.status == "success"
    assert response.records_extracted >= 4
    assert response.records_normalized >= 4
    assert response.parsed_fragments_summary["json_fragments"] >= 2
    assert response.parsed_fragments_summary["kv_pairs"] >= 2

    schema = schema_service.get_current_schema(source_id)
    field_names = {field.name for field in schema.fields}
    assert {
        "transaction_id",
        "amount",
        "currency",
        "payment_method",
        "status",
        "session_id",
        "device_type",
    }.issubset(field_names)

    status_query = query_service.execute_query(source_id, {"filter": {"status": "completed"}})
    assert status_query.result_count >= 1
    assert status_query.results[0]["status"] == "completed"

    currency_query = query_service.execute_query(source_id, {"filter": {"currency": "USD"}})
    assert currency_query.result_count >= 1
    assert currency_query.results[0]["currency"] == "USD"


@pytest.mark.integration
def test_markdown_upload_with_code_blocks_and_html(tmp_path):
    """Ensure markdown files with JSON and HTML code blocks are processed."""

    source_id = "demo-markdown"
    file_content = TEST_PAYLOADS["test_case_21_embedded_code_block_fences"]

    sample_file = tmp_path / "sample_input.md"
    sample_file.write_text(file_content)

    response = process_upload(str(sample_file), source_id)

    assert response.status == "success"
    assert response.records_extracted >= 1
    assert response.records_normalized >= 1
    assert response.parsed_fragments_summary["json_fragments"] >= 1

    schema = schema_service.get_current_schema(source_id)
    field_names = {field.name for field in schema.fields}
    assert {"user_id", "username", "email", "actual_field", "real_data"}.issubset(field_names)

    json_block_query = query_service.execute_query(source_id, {"filter": {"user_id": 8888}})
    assert json_block_query.result_count == 1
    assert json_block_query.results[0]["username"] == "code_block_user"

    kv_query = query_service.execute_query(source_id, {"filter": {"actual_field": "actual_value"}})
    assert kv_query.result_count == 1
    assert kv_query.results[0]["real_data"] == "this is real"


@pytest.mark.integration
def test_multiple_fragments_with_complex_queries(tmp_path):
    """Handle multiple Tier A fragments and run advanced queries."""

    source_id = "demo-complex"
    file_content = TEST_PAYLOADS["test_case_1_simple_valid_json"]

    sample_file = tmp_path / "sample_complex.txt"
    sample_file.write_text(file_content)

    response = process_upload(str(sample_file), source_id)

    assert response.status == "success"
    assert response.records_extracted >= 2
    assert response.records_normalized >= 2

    schema = schema_service.get_current_schema(source_id)
    field_names = {field.name for field in schema.fields}
    assert {"user_id", "username", "email", "balance", "active", "signup_date"}.issubset(field_names)

    balance_query = query_service.execute_query(source_id, {"filter": {"balance": {"$gt": 1000}}})
    assert balance_query.result_count == 1
    assert balance_query.results[0]["username"] == "alice_wonder"

    inactive_query = query_service.execute_query(source_id, {"filter": {"active": False}})
    assert inactive_query.result_count == 1
    assert inactive_query.results[0]["username"] == "bob_smith"

    sorted_query = query_service.execute_query(
        source_id,
        {
            "filter": {"signup_date": {"$exists": True}},
            "sort": [["signup_date", -1]],
            "limit": 1,
        },
    )
    assert sorted_query.result_count == 1
    assert sorted_query.results[0]["user_id"] == 1002