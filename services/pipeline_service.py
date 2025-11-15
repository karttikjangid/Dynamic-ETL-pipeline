"""Pipeline service orchestrating extraction → normalization → storage."""

from __future__ import annotations

from typing import Tuple

from core import UploadResponse


def process_upload(file_path: str, source_id: str) -> UploadResponse:
    """Process a newly uploaded file and return upload metadata."""

    raise NotImplementedError


def get_database_name(source_id: str) -> str:
    """Return deterministic database name for a source."""

    raise NotImplementedError


def get_collection_name(source_id: str) -> str:
    """Return deterministic collection name for a source."""

    raise NotImplementedError
