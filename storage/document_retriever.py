"""Document retrieval helpers."""

from __future__ import annotations

from typing import Dict, List, Optional


def get_documents(
    db, name: str, limit: int = 100, filter_query: Optional[Dict] = None
) -> List[Dict]:
    """Fetch a limited set of documents."""

    raise NotImplementedError


def count_documents(db, name: str, filter_query: Optional[Dict] = None) -> int:
    """Return the count of documents matching a filter."""

    raise NotImplementedError


def get_document_by_id(db, name: str, doc_id) -> Optional[Dict]:
    """Retrieve a document by its identifier."""

    raise NotImplementedError
