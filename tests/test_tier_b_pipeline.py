"""Tier B robustness tests for the Dynamic ETL pipeline."""

from __future__ import annotations

from pathlib import Path

import pytest

from services.pipeline_service import process_upload
from services import query_service, schema_service


FIXTURE_DIR = Path(__file__).resolve().parents[1] / "test_data" / "tier_b"


def _fixture_path(filename: str) -> str:
    """Return an absolute path to a Tier-B fixture file."""

    path = FIXTURE_DIR / filename
    if not path.is_file():
        raise FileNotFoundError(f"Tier-B fixture not found: {path}")
    return str(path)


@pytest.mark.integration
def test_tier_b01_mixed_formats():
    source_id = "tier-b-01"
    file_path = _fixture_path("B-01-mixed-formats.txt")

    response = process_upload(file_path, source_id)

    assert response.status == "success"
    assert response.parsed_fragments_summary["json_fragments"] >= 1
    assert response.parsed_fragments_summary["html_tables"] >= 1
    assert response.parsed_fragments_summary["csv_blocks"] >= 1
    assert response.records_extracted >= 3

    schema = schema_service.get_current_schema(source_id)
    field_names = {field.name for field in schema.fields}
    assert {"inventory_id", "source_system", "collection_hint"}.issubset(field_names)


@pytest.mark.integration
def test_tier_b02_frontmatter_inline_html():
    source_id = "tier-b-02"
    file_path = _fixture_path("B-02-frontmatter-inline-html.md")

    response = process_upload(file_path, source_id)

    assert response.status == "success"
    assert response.records_extracted >= 1

    schema = schema_service.get_current_schema(source_id)
    field_names = {field.name for field in schema.fields}
    assert {"title", "version", "status", "approver"}.issubset(field_names)


@pytest.mark.integration
def test_tier_b03_html_with_scripts():
    source_id = "tier-b-03"
    file_path = _fixture_path("B-03-html-with-scripts.txt")

    response = process_upload(file_path, source_id)

    assert response.status == "success"
    assert response.parsed_fragments_summary["json_fragments"] >= 1

    schema = schema_service.get_current_schema(source_id)
    field_names = {field.name for field in schema.fields}
    assert {"customer_id", "page_section", "status"}.issubset(field_names)


@pytest.mark.integration
def test_tier_b04_multiple_json_fragments():
    source_id = "tier-b-04"
    file_path = _fixture_path("B-04-mixed-json.txt")

    response = process_upload(file_path, source_id)

    assert response.status == "success"
    assert response.parsed_fragments_summary["json_fragments"] >= 3

    query = query_service.execute_query(
        source_id,
        {"filter": {"record": 2}},
    )
    assert query.result_count == 1


@pytest.mark.integration
def test_tier_b05_inline_sql_is_treated_as_text():
    source_id = "tier-b-05"
    file_path = _fixture_path("B-05-inline-sql.txt")

    response = process_upload(file_path, source_id)

    assert response.status == "success"
    assert response.records_extracted >= 1

    query = query_service.execute_query(source_id, {"filter": {"system": "analytics"}})
    assert query.result_count == 1


@pytest.mark.integration
def test_tier_b06_csv_inconsistent_quotes():
    source_id = "tier-b-06"
    file_path = _fixture_path("B-06-inconsistent-csv.txt")

    response = process_upload(file_path, source_id)

    assert response.status == "success"
    assert response.records_extracted >= 1

    schema = schema_service.get_current_schema(source_id)
    field_names = {field.name for field in schema.fields}
    assert {"summary", "csv_hint"}.issubset(field_names)


@pytest.mark.integration
def test_tier_b07_mixed_delimiter_block():
    source_id = "tier-b-07"
    file_path = _fixture_path("B-07-mixed-delimiters.txt")

    response = process_upload(file_path, source_id)

    assert response.status == "success"
    assert response.records_extracted >= 1

    query = query_service.execute_query(source_id, {"filter": {"report_id": "MIX-DELIM"}})
    assert query.result_count == 1


@pytest.mark.integration
def test_tier_b08_markdown_nested_lists():
    source_id = "tier-b-08"
    file_path = _fixture_path("B-08-markdown-nested-lists.md")

    response = process_upload(file_path, source_id)

    assert response.status == "success"
    assert response.parsed_fragments_summary["json_fragments"] >= 1

    schema = schema_service.get_current_schema(source_id)
    field_names = {field.name for field in schema.fields}
    assert {"region", "customers", "revenue", "summary"}.issubset(field_names)


@pytest.mark.integration
def test_tier_b09_timezone_date_mix():
    source_id = "tier-b-09"
    file_path = _fixture_path("B-09-timezone-dates.txt")

    response = process_upload(file_path, source_id)

    assert response.status == "success"
    assert response.parsed_fragments_summary["json_fragments"] >= 1

    schema = schema_service.get_current_schema(source_id)
    field_names = {field.name for field in schema.fields}
    assert {"iso_date", "us_date", "eu_date", "observed_at"}.issubset(field_names)


@pytest.mark.integration
def test_tier_b10_multi_separator_kv():
    source_id = "tier-b-10"
    file_path = _fixture_path("B-10-multi-separator-kv.txt")

    response = process_upload(file_path, source_id)

    assert response.status == "success"
    assert response.parsed_fragments_summary["kv_pairs"] >= 1

    query = query_service.execute_query(source_id, {"filter": {"priority": "high"}})
    assert query.result_count == 1
