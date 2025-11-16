"""Group tabular fragments into SQLite tables using field + NER similarity."""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha1
from typing import Any, Dict, Iterable, List, Set

from core import SchemaField, TabularSchemaGroup
from utils.logger import get_logger

LOGGER = get_logger(__name__)

FIELD_SIMILARITY_THRESHOLD = 0.7
NER_SIMILARITY_THRESHOLD = 0.5

_EXCLUDED_COLUMNS = {"ner"}


@dataclass
class TabularGroupPlan:
    """Internal representation of a table creation/insertion plan."""

    group: TabularSchemaGroup
    documents: List[Dict[str, Any]] = field(default_factory=list)


def group_tabular_documents(
    documents: List[Dict[str, Any]],
    source_id: str,
    version: int,
) -> List[TabularGroupPlan]:
    """Cluster tabular documents by comparing fields and NER labels."""

    if not documents:
        return []

    buckets: List[_GroupingBucket] = []

    for doc in documents:
        field_names = _extract_field_names(doc)
        ner_labels = _extract_ner_labels(doc)

        assigned = False
        for bucket in buckets:
            if bucket.is_compatible(field_names, ner_labels):
                bucket.add_document(doc, field_names, ner_labels)
                assigned = True
                break

        if not assigned:
            bucket_id = f"grp_{len(buckets) + 1:02d}"
            new_bucket = _GroupingBucket(bucket_id)
            new_bucket.add_document(doc, field_names, ner_labels)
            buckets.append(new_bucket)

    plans: List[TabularGroupPlan] = []
    for bucket in buckets:
        schema_fields = _infer_schema_fields(bucket.documents)
        signature = _build_signature(schema_fields, bucket.ner_labels)
        table_name = _build_table_name(source_id, version, signature)
        ner_labels_sorted = sorted(bucket.ner_labels)
        group = TabularSchemaGroup(
            group_id=bucket.bucket_id,
            table_name=table_name,
            signature=signature,
            fields=schema_fields,
            record_count=len(bucket.documents),
            ner_labels=ner_labels_sorted or None,
        )
        plans.append(TabularGroupPlan(group=group, documents=bucket.documents))

    LOGGER.info(
        "Clustered %d tabular documents for source '%s' version %d into %d table(s)",
        len(documents),
        source_id,
        version,
        len(plans),
    )
    return plans


class _GroupingBucket:
    """Helper container for grouping state."""

    def __init__(self, bucket_id: str) -> None:
        self.bucket_id = bucket_id
        self.documents: List[Dict[str, Any]] = []
        self.field_names: Set[str] = set()
        self.ner_labels: Set[str] = set()

    def is_compatible(self, fields: Set[str], ner_labels: Set[str]) -> bool:
        field_score = _jaccard(self.field_names, fields)
        ner_score = _jaccard(self.ner_labels, ner_labels)
        return field_score >= FIELD_SIMILARITY_THRESHOLD and ner_score >= NER_SIMILARITY_THRESHOLD

    def add_document(
        self,
        doc: Dict[str, Any],
        fields: Set[str],
        ner_labels: Set[str],
    ) -> None:
        self.documents.append(doc)
        self.field_names.update(fields)
        self.ner_labels.update(ner_labels)


def _extract_field_names(doc: Dict[str, Any]) -> Set[str]:
    fields: Set[str] = set()
    for key in doc.keys():
        if key in _EXCLUDED_COLUMNS or key.startswith("_"):
            continue
        fields.add(str(key))
    return fields


def _extract_ner_labels(doc: Dict[str, Any]) -> Set[str]:
    ner_payload = doc.get("ner")
    if not isinstance(ner_payload, dict):
        return set()
    labels: Set[str] = set()
    for label, values in ner_payload.items():
        if not isinstance(label, str):
            continue
        if isinstance(values, list) and not values:
            continue
        labels.add(label)
    return labels


def _infer_schema_fields(documents: List[Dict[str, Any]]) -> List[SchemaField]:
    field_info: Dict[str, Dict[str, Any]] = {}
    total_docs = len(documents)
    for doc in documents:
        for key, value in doc.items():
            if key in _EXCLUDED_COLUMNS or key.startswith("_"):
                continue
            info = field_info.setdefault(
                key,
                {
                    "example": None,
                    "types": set(),
                    "count": 0,
                    "saw_null": False,
                },
            )
            info["count"] += 1
            if value is None:
                info["saw_null"] = True
            elif info["example"] is None:
                info["example"] = value
            info["types"].add(_map_python_type(value))
    schema_fields = [
        SchemaField(
            name=name,
            type=_select_type(metadata["types"]),
            nullable=metadata["saw_null"] or metadata["count"] < total_docs,
            example_value=metadata["example"],
        )
        for name, metadata in field_info.items()
    ]
    schema_fields.sort(key=lambda field: field.name)
    return schema_fields


def _map_python_type(value: Any) -> str:
    if value is None:
        return "string"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int) and not isinstance(value, bool):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, dict):
        return "object"
    if isinstance(value, list):
        return "array"
    return "string"


def _select_type(types: Iterable[str]) -> str:
    priority = ["integer", "number", "boolean", "object", "array", "string"]
    types_set = set(types)
    for candidate in priority:
        if candidate in types_set:
            return candidate
    return "string"


def _build_signature(fields: List[SchemaField], ner_labels: Set[str]) -> str:
    hasher = sha1()
    for field in sorted(fields, key=lambda f: f.name):
        hasher.update(field.name.encode("utf-8"))
        hasher.update(field.type.encode("utf-8"))
    for label in sorted(ner_labels):
        hasher.update(label.encode("utf-8"))
    return hasher.hexdigest()


def _build_table_name(source_id: str, version: int, signature: str) -> str:
    safe_source = _sanitize_identifier(source_id)
    return f"{safe_source}_v{version}_{signature[:8]}"


def _sanitize_identifier(value: str) -> str:
    allowed = [c if c.isalnum() else "_" for c in value]
    sanitized = "".join(allowed)
    return sanitized.strip("_") or "source"


def _jaccard(left: Set[str], right: Set[str]) -> float:
    if not left and not right:
        return 1.0
    if not left or not right:
        return 0.0
    intersection = left & right
    union = left | right
    if not union:
        return 0.0
    return len(intersection) / len(union)