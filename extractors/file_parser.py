"""Helpers for reading and parsing supported file types."""

from __future__ import annotations

from pathlib import Path
from typing import List


def parse_file(file_path: str) -> str:
    """Dispatch parsing based on extension."""

    path = Path(file_path)
    suffix = path.suffix.lower()
    if suffix == ".md":
        return parse_md_file(file_path)
    if suffix == ".txt":
        return parse_txt_file(file_path)
    raise ValueError(f"Unsupported file type: {suffix}")


def parse_txt_file(file_path: str) -> str:
    """Return plain text content."""

    raise NotImplementedError


def parse_md_file(file_path: str) -> str:
    """Return markdown content as-is."""

    raise NotImplementedError


def extract_code_blocks(md_content: str) -> List[str]:
    """Extract fenced code blocks from Markdown content."""

    raise NotImplementedError
