"""Smoke tests for individual extractors using shared Tier-A payloads."""

from __future__ import annotations

from extractors.json_extractor import JSONExtractor
from extractors.kv_extractor import KVExtractor
from tests.payloads import TEST_PAYLOADS


EXTRACTION_TEXT = TEST_PAYLOADS["test_case_7_mixed_json_and_kv_same_file"]


def test_json_extractor_finds_multiple_fragments():
    extractor = JSONExtractor()
    records = extractor.extract(EXTRACTION_TEXT)

    assert len(records) >= 2
    transaction_record = next((rec for rec in records if rec.data.get("transaction_id")), None)
    session_record = next((rec for rec in records if rec.data.get("session_id")), None)

    assert transaction_record is not None
    assert session_record is not None
    assert transaction_record.data["currency"] == "USD"
    assert session_record.data["duration_seconds"] == 3600


def test_kv_extractor_captures_payment_metadata():
    extractor = KVExtractor()
    records = extractor.extract(EXTRACTION_TEXT)

    assert len(records) >= 2
    payment_record = next((rec for rec in records if rec.data.get("payment_method")), None)
    device_record = next((rec for rec in records if rec.data.get("device_type")), None)

    assert payment_record is not None
    assert device_record is not None
    assert payment_record.data["status"] == "completed"
    assert device_record.data["browser"].lower() == "chrome"