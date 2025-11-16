"""Utilities for determining SQLite file paths per schema version."""

from __future__ import annotations

from pathlib import Path

from config import get_settings


def get_version_db_path(source_id: str, version: int) -> str:
    settings = get_settings()
    base_dir = getattr(settings, "sqlite_base_dir", None)
    if not base_dir:
        base_dir = Path(settings.sqlite_db_path).expanduser().resolve().parent
    root = Path(base_dir).expanduser().resolve()
    safe_source = _sanitize_identifier(source_id)
    version_dir = root / safe_source
    version_dir.mkdir(parents=True, exist_ok=True)
    db_path = version_dir / f"v{version}.db"
    return str(db_path)


def _sanitize_identifier(value: str) -> str:
    allowed = [c if c.isalnum() else "_" for c in value]
    sanitized = "".join(allowed)
    return sanitized.strip("_") or "source"
