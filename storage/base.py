"""Abstract storage contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from core import SchemaMetadata


class BaseStorage(ABC):
    """Interface for storage backends."""

    @abstractmethod
    def create_collection(self, name: str, schema: SchemaMetadata) -> bool:
        raise NotImplementedError

    @abstractmethod
    def insert_documents(self, name: str, docs: List[Dict]) -> int:
        raise NotImplementedError

    @abstractmethod
    def get_documents(self, name: str, limit: int, filter_query: Optional[Dict] = None) -> List[Dict]:
        raise NotImplementedError

    @abstractmethod
    def execute_query(self, name: str, query: Dict) -> List[Dict]:
        raise NotImplementedError
