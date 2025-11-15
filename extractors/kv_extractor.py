"""Key-value extraction utilities."""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from core import ExtractedRecord

from .base import BaseExtractor


class KVExtractor(BaseExtractor):
    """Extractor for structured key-value sections."""

    def extract(self, content: str) -> List[ExtractedRecord]:
        raise NotImplementedError


def extract_key_value_pairs(text: str) -> List[Dict[str, str]]:
    """Return normalized key-value dictionaries."""

    raise NotImplementedError


def find_kv_sections(text: str) -> List[str]:
    """Locate sections likely containing key-value pairs."""

    raise NotImplementedError


def parse_kv_line(line: str) -> Optional[Tuple[str, str]]:
    """Parse a line into a key/value tuple if possible."""

    raise NotImplementedError
