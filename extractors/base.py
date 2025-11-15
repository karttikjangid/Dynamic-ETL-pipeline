"""Abstract base class for extractors."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from core import ExtractedRecord


class BaseExtractor(ABC):
    """Every extractor must implement the extract contract."""

    @abstractmethod
    def extract(self, content: str) -> List[ExtractedRecord]:
        """Extract structured records from raw content."""

        raise NotImplementedError
