"""JSON fragment extraction utilities."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from core import ExtractedRecord

from .base import BaseExtractor


class JSONExtractor(BaseExtractor):
    """Extractor for JSON fragments and code blocks."""

    def extract(self, content: str) -> List[ExtractedRecord]:
        raise NotImplementedError


def extract_json_fragments(text: str) -> List[Dict[str, Any]]:
    """Find and parse JSON blobs within text."""

    raise NotImplementedError


def find_json_patterns(text: str) -> List[str]:
    """Return candidate JSON strings from raw text."""

    raise NotImplementedError


def parse_json_string(json_str: str) -> Optional[Dict[str, Any]]:
    """Safely parse a JSON string."""

    raise NotImplementedError
