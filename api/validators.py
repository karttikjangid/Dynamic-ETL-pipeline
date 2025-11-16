"""Input validators for API payloads."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import HTTPException, UploadFile
from starlette import status

ALLOWED_EXTENSIONS = {".txt", ".md", ".pdf"}
SAFE_SOURCE_ID_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+$")
MAX_SOURCE_ID_LENGTH = 60


def validate_upload_payload(
    file: Optional[UploadFile],
    source_id: Optional[str],
    version: Optional[int],
) -> Dict[str, Any]:
    """Validate upload payload structure and return normalized values."""

    if file is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File payload is required.")

    filename = file.filename or ""
    if not filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file must have a name.")

    extension = Path(filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Unsupported file extension "
                f"'{extension or 'unknown'}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}. "
                "PDF uploads must contain selectable (non-image) text."
            ),
        )

    normalized_source_id: Optional[str] = None
    if source_id:
        normalized_source_id = source_id.strip()
        if not normalized_source_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="source_id cannot be empty.")
        if len(normalized_source_id) > MAX_SOURCE_ID_LENGTH:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"source_id cannot exceed {MAX_SOURCE_ID_LENGTH} characters.",
            )
        if not SAFE_SOURCE_ID_PATTERN.match(normalized_source_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="source_id may only contain letters, numbers, underscores, hyphens, and periods.",
            )

    if version is not None:
        if version <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="version must be a positive integer.")

    return {
        "source_id": normalized_source_id,
        "version": version,
        "extension": extension,
    }


def validate_query_payload(payload: Dict[str, Any]) -> None:
    """Validate strict query payloads."""

    if not isinstance(payload, dict):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Query payload must be a JSON object.")

    if not payload:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Query payload cannot be empty.")

    engine = payload.get("engine")
    if engine is not None:
        if not isinstance(engine, str):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="engine must be a string.")
        normalized_engine = engine.lower()
        if normalized_engine not in {"mongodb", "sqlite"}:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="engine must be either 'mongodb' or 'sqlite'.")

    # Reject natural-language strings masquerading as queries to enforce strict structured queries.
    if any(
        isinstance(value, str) and value.strip().split(" ")[0].lower() in {"select", "find", "show"}
        for key, value in payload.items()
        if key not in {"engine"}
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Natural language or raw textual queries are not supported. Provide a structured dict payload.",
        )

