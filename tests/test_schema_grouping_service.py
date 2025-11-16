"""Unit tests for schema grouping heuristics."""

from services.schema_grouping_service import group_tabular_documents


def test_grouping_merges_similar_fragments():
    documents = [
        {
            "account_id": "A-1",
            "balance": 1250.0,
            "status": "active",
            "ner": {"ORG": ["Acme"]},
        },
        {
            "account_id": "A-2",
            "balance": 980.5,
            "status": "inactive",
            "ner": {"ORG": ["Acme"]},
        },
    ]

    plans = group_tabular_documents(documents, "demo", 1)

    assert len(plans) == 1
    assert plans[0].group.record_count == 2
    assert {field.name for field in plans[0].group.fields} == {"account_id", "balance", "status"}


def test_grouping_splits_dissimilar_fragments():
    documents = [
        {
            "account_id": "A-1",
            "balance": 1250.0,
            "ner": {"ORG": ["Acme"]},
        },
        {
            "ticket_id": "T-1",
            "ticket_tier": "tier-b",
            "response_minutes": 30,
            "ner": {"PRODUCT": ["Widget"], "GPE": ["NY"]},
        },
    ]

    plans = group_tabular_documents(documents, "demo", 1)

    assert len(plans) == 2
    doc_counts = sorted(plan.group.record_count for plan in plans)
    assert doc_counts == [1, 1]
    table_names = {plan.group.table_name for plan in plans}
    assert len(table_names) == 2
