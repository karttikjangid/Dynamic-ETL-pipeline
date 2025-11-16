"""End-to-end service tests using a mongomock-backed MongoDB."""

from __future__ import annotations

from pathlib import Path

import pytest

from typing import Iterable, Set

from services.pipeline_service import process_upload
from services import query_service, schema_service
from tests.payloads import TEST_PAYLOADS


def _get_table_with_fields(schema, required_fields: Iterable[str]) -> str:
    required: Set[str] = set(required_fields)
    assert required, "required_fields cannot be empty"
    assert schema.tabular_groups, "Expected at least one tabular group"
    for group in schema.tabular_groups:
        field_names = {field.name for field in group.fields}
        if required.issubset(field_names):
            return group.table_name
    raise AssertionError(f"No tabular group contains fields: {sorted(required)}")


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
    assert schema.tabular_groups and len(schema.tabular_groups) >= 1

    table_name = _get_table_with_fields(
        schema,
        ["transaction_id", "status", "amount"],
    )

    status_query = query_service.execute_query(
        source_id,
        {
            "engine": "sqlite",
            "table": table_name,
            "select": ["transaction_id", "status", "amount"],
            "where": {"status": "completed"},
            "limit": 10,
        },
    )
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

    kv_table = _get_table_with_fields(schema, ["actual_field", "real_data"])

    kv_query = query_service.execute_query(
        source_id,
        {
            "engine": "sqlite",
            "table": kv_table,
            "select": ["actual_field", "real_data"],
            "where": {"actual_field": "actual_value"},
        },
    )
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


@pytest.mark.integration
def test_sqlite_engine_query_execution(tmp_path):
    """Ensure SQLite-routed sources can be queried via the new engine flag."""

    source_id = "demo-sqlite"
    repo_root = Path(__file__).resolve().parents[1]
    template_path = repo_root / "test_data" / "sample_tier_b_sqlite.txt"

    if not template_path.is_file():
        pytest.skip("SQLite sample file not found; skipping test.")

    sample_file = tmp_path / "sample_sqlite.txt"
    sample_file.write_text(template_path.read_text())

    response = process_upload(str(sample_file), source_id)

    assert response.status == "success"
    assert response.evidence is not None
    assert response.evidence["storage"].get("sqlite_inserted", 0) >= 1

    schema = schema_service.get_current_schema(source_id)
    assert "sqlite" in schema.compatible_dbs
    assert schema.tabular_groups and len(schema.tabular_groups) >= 1

    # Query CSV-derived account balances using SQLite engine
    account_table = _get_table_with_fields(
        schema,
        ["account_id", "branch_code", "currency", "balance", "status"],
    )

    account_query = query_service.execute_query(
        source_id,
        {
            "engine": "sqlite",
            "table": account_table,
            "select": ["account_id", "branch_code", "currency", "balance", "status"],
            "where": {
                "status": "active",
                "balance": {"$gt": 9000},
            },
            "order_by": [["balance", "desc"]],
            "limit": 5,
        },
    )

    assert account_query.result_count >= 1
    assert all(row["status"] == "active" for row in account_query.results)
    assert account_query.query["engine"] == "sqlite"

    # Query HTML-derived SLA rows using pattern matching
    sla_table = _get_table_with_fields(
        schema,
        ["branch_code", "ticket_tier", "response_minutes", "resolution_hours"],
    )

    sla_query = query_service.execute_query(
        source_id,
        {
            "engine": "sqlite",
            "table": sla_table,
            "select": ["branch_code", "ticket_tier", "response_minutes", "resolution_hours"],
            "where": {
                "ticket_tier": {"$like": "tier-b%"},
                "response_minutes": {"$lte": 60},
            },
            "order_by": [["response_minutes", "asc"]],
        },
    )

    assert sla_query.result_count == 2
    assert {row["ticket_tier"] for row in sla_query.results} == {"tier-b"}


@pytest.mark.integration
def test_mixed_tier_b_fixture_supports_dual_storage(tmp_path):
    """Ensure Tier B mixed-format uploads still materialize SQLite tables."""

    source_id = "tier-b-mixed"
    repo_root = Path(__file__).resolve().parents[1]
    fixture_path = repo_root / "test_data" / "tier_b" / "B-01-mixed-formats.txt"

    if not fixture_path.is_file():
        pytest.skip("Tier B mixed-format fixture missing; skipping test.")

    sample_file = tmp_path / "b01_mixed.txt"
    sample_file.write_text(fixture_path.read_text())

    response = process_upload(str(sample_file), source_id)

    assert response.status == "success"
    assert response.evidence is not None
    storage_evidence = response.evidence.get("storage", {})
    assert storage_evidence.get("sqlite_inserted", 0) >= 1
    assert storage_evidence.get("mongodb_inserted", 0) >= 1

    schema = schema_service.get_current_schema(source_id)
    assert {"sqlite", "mongodb"}.issubset(schema.compatible_dbs)
    assert schema.tabular_groups and len(schema.tabular_groups) >= 1

    sqlite_table = _get_table_with_fields(
        schema,
        ["account_id", "status", "balance", "region"],
    )

    sqlite_query = query_service.execute_query(
        source_id,
        {
            "engine": "sqlite",
            "table": sqlite_table,
            "select": ["account_id", "status", "balance", "region"],
            "where": {"status": "active"},
            "limit": 5,
        },
    )

    assert sqlite_query.result_count >= 1
    assert all(row["status"] == "active" for row in sqlite_query.results)