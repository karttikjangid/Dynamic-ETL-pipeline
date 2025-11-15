"""Tier B robustness tests for the Dynamic ETL pipeline."""

from __future__ import annotations

from uuid import uuid4

import pytest

from services.pipeline_service import process_upload
from services import query_service, schema_service
from tests.payloads import TEST_PAYLOADS


def _write_payload(tmp_path, content: str, suffix: str = ".txt") -> str:
    file_path = tmp_path / f"tier_b_{uuid4().hex}{suffix}"
    file_path.write_text(content)
    return str(file_path)


@pytest.mark.integration
def test_tier_b01_mixed_formats(tmp_path):
    source_id = "tier-b-01"
    file_path = _write_payload(tmp_path, TEST_PAYLOADS["tier_b_01_mixed_formats"])

    response = process_upload(file_path, source_id)

    assert response.status == "success"
    assert response.parsed_fragments_summary["json_fragments"] >= 1
    assert response.records_extracted >= 2

    schema = schema_service.get_current_schema(source_id)
    field_names = {field.name for field in schema.fields}
    assert {"inventory_id", "source_system", "collection_hint"}.issubset(field_names)


@pytest.mark.integration
def test_tier_b02_frontmatter_inline_html(tmp_path):
    source_id = "tier-b-02"
    file_path = _write_payload(
        tmp_path,
        TEST_PAYLOADS["tier_b_02_frontmatter_inline_html"],
        suffix=".md",
    )

    response = process_upload(file_path, source_id)

    assert response.status == "success"
    assert response.records_extracted >= 1

    schema = schema_service.get_current_schema(source_id)
    field_names = {field.name for field in schema.fields}
    assert {"title", "version", "status", "approver"}.issubset(field_names)


@pytest.mark.integration
def test_tier_b03_html_with_scripts(tmp_path):
    source_id = "tier-b-03"
    file_path = _write_payload(tmp_path, TEST_PAYLOADS["tier_b_03_html_with_scripts"])

    response = process_upload(file_path, source_id)

    assert response.status == "success"
    assert response.parsed_fragments_summary["json_fragments"] >= 1

    schema = schema_service.get_current_schema(source_id)
    field_names = {field.name for field in schema.fields}
    assert {"customer_id", "page_section", "status"}.issubset(field_names)


@pytest.mark.integration
def test_tier_b04_multiple_json_fragments(tmp_path):
    source_id = "tier-b-04"
    file_path = _write_payload(tmp_path, TEST_PAYLOADS["tier_b_04_multiple_json_fragments"])

    response = process_upload(file_path, source_id)

    assert response.status == "success"
    assert response.parsed_fragments_summary["json_fragments"] >= 3

    query = query_service.execute_query(
        source_id,
        {"filter": {"record": 2}},
    )
    assert query.result_count == 1


@pytest.mark.integration
def test_tier_b05_inline_sql_is_treated_as_text(tmp_path):
    source_id = "tier-b-05"
    file_path = _write_payload(tmp_path, TEST_PAYLOADS["tier_b_05_inline_sql"])

    response = process_upload(file_path, source_id)

    assert response.status == "success"
    assert response.records_extracted >= 1

    query = query_service.execute_query(source_id, {"filter": {"system": "analytics"}})
    assert query.result_count == 1


@pytest.mark.integration
def test_tier_b06_csv_inconsistent_quotes(tmp_path):
    source_id = "tier-b-06"
    file_path = _write_payload(tmp_path, TEST_PAYLOADS["tier_b_06_csv_inconsistent_quotes"])

    response = process_upload(file_path, source_id)

    assert response.status == "success"
    assert response.records_extracted >= 1

    schema = schema_service.get_current_schema(source_id)
    field_names = {field.name for field in schema.fields}
    assert {"summary", "csv_hint"}.issubset(field_names)


@pytest.mark.integration
def test_tier_b07_mixed_delimiter_block(tmp_path):
    source_id = "tier-b-07"
    file_path = _write_payload(tmp_path, TEST_PAYLOADS["tier_b_07_mixed_delimiter_block"])

    response = process_upload(file_path, source_id)

    assert response.status == "success"
    assert response.records_extracted >= 1

    query = query_service.execute_query(source_id, {"filter": {"report_id": "MIX-DELIM"}})
    assert query.result_count == 1


@pytest.mark.integration
def test_tier_b08_markdown_nested_lists(tmp_path):
    source_id = "tier-b-08"
    file_path = _write_payload(
        tmp_path,
        TEST_PAYLOADS["tier_b_08_markdown_nested_lists"],
        suffix=".md",
    )

    response = process_upload(file_path, source_id)

    assert response.status == "success"
    assert response.parsed_fragments_summary["json_fragments"] >= 1

    schema = schema_service.get_current_schema(source_id)
    field_names = {field.name for field in schema.fields}
    assert {"region", "customers", "revenue", "summary"}.issubset(field_names)


@pytest.mark.integration
def test_tier_b09_timezone_date_mix(tmp_path):
    source_id = "tier-b-09"
    file_path = _write_payload(tmp_path, TEST_PAYLOADS["tier_b_09_timezone_date_mix"])

    response = process_upload(file_path, source_id)

    assert response.status == "success"
    assert response.parsed_fragments_summary["json_fragments"] >= 1

    schema = schema_service.get_current_schema(source_id)
    field_names = {field.name for field in schema.fields}
    assert {"iso_date", "us_date", "eu_date", "observed_at"}.issubset(field_names)


@pytest.mark.integration
def test_tier_b10_multi_separator_kv(tmp_path):
    source_id = "tier-b-10"
    file_path = _write_payload(tmp_path, TEST_PAYLOADS["tier_b_10_multi_separator_kv"])

    response = process_upload(file_path, source_id)

    assert response.status == "success"
    assert response.parsed_fragments_summary["kv_pairs"] >= 1

    query = query_service.execute_query(source_id, {"filter": {"priority": "high"}})
    assert query.result_count == 1
