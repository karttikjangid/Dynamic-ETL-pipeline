"""Utility helpers for basic file interactions."""

from __future__ import annotations

from pathlib import Path


def read_text_file(file_path: str) -> str:
    """Read a UTF-8 text file."""

    raise NotImplementedError


def write_text_file(file_path: str, content: str) -> None:
    """Write content to a UTF-8 text file."""

    raise NotImplementedError


def ensure_directory(path: str) -> Path:
    """Ensure that a directory exists."""

    raise NotImplementedError
