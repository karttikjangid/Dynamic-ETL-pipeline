"""Document insertion helpers."""

from __future__ import annotations

from typing import Dict, List

from core import SchemaMetadata


def insert_documents(db, name: str, docs: List[Dict]) -> int:
    """Insert documents sequentially."""

    raise NotImplementedError


def batch_insert_documents(
    db, name: str, docs: List[Dict], batch_size: int = 100
) -> int:
    """Insert documents in batches for efficiency."""

    raise NotImplementedError


def validate_document_for_insertion(doc: Dict, schema: SchemaMetadata) -> bool:
    """Ensure documents comply with schema prior to insertion."""

    raise NotImplementedError
