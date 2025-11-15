"""Abstract base class for record normalizers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List

from core import NormalizedRecord


class BaseNormalizer(ABC):
    """Normalize raw extracted payloads into structured data."""

    @abstractmethod
    def normalize(self, records: List[Dict]) -> List[NormalizedRecord]:
        raise NotImplementedError
