"""HTML table normalizer for Tier-B pipeline."""

from typing import Any, Dict, List

from core.models import NormalizedRecord
from normalizers.base import BaseNormalizer
from utils.logger import get_logger

logger = get_logger(__name__)


class HTMLTableNormalizer(BaseNormalizer):
    """Normalizes HTML table data extracted from documents."""

    def normalize(self, data: Any, metadata: Dict[str, Any]) -> List[NormalizedRecord]:
        """Normalize HTML table rows into standardized records.
        
        Args:
            data: List of row dictionaries from HTML table
            metadata: Metadata from extraction including table_id, headers, etc.
            
        Returns:
            List of NormalizedRecord objects
        """
        if not isinstance(data, list):
            logger.warning(f"Expected list for HTML table data, got {type(data)}")
            return []
        
        normalized_records = []
        
        for idx, row in enumerate(data):
            if not isinstance(row, dict):
                logger.warning(f"Row {idx} is not a dict, skipping")
                continue
            
            # Standardize keys (lowercase with underscores)
            normalized_data = {}
            for key, value in row.items():
                normalized_key = self._standardize_key(key)
                normalized_value = self._infer_type(value)
                normalized_data[normalized_key] = normalized_value
            
            # Create normalized record
            record = NormalizedRecord(
                data=normalized_data,
                source_type="html_table",
                extraction_confidence=metadata.get("confidence", 0.95),
                provenance={
                    "table_id": metadata.get("table_id"),
                    "row_index": idx,
                    "offset_start": metadata.get("offset_start"),
                    "offset_end": metadata.get("offset_end"),
                    "headers": metadata.get("headers", [])
                }
            )
            normalized_records.append(record)
        
        logger.info(f"Normalized {len(normalized_records)} HTML table row(s)")
        return normalized_records

    def _standardize_key(self, key: str) -> str:
        """Standardize column names to lowercase with underscores.
        
        Args:
            key: Original column name
            
        Returns:
            Standardized key
        """
        import re
        # Convert to lowercase
        key = key.lower()
        # Replace spaces and special chars with underscore
        key = re.sub(r'[^\w]+', '_', key)
        # Remove leading/trailing underscores
        key = key.strip('_')
        return key or "unknown"

    def _infer_type(self, value: str) -> Any:
        """Attempt to infer and cast the type of a value.
        
        Args:
            value: String value from table cell
            
        Returns:
            Value cast to appropriate type
        """
        if not isinstance(value, str):
            return value
        
        value = value.strip()
        
        if not value:
            return None
        
        # Try integer
        try:
            if '.' not in value and ',' not in value:
                return int(value)
        except ValueError:
            pass
        
        # Try float
        try:
            return float(value.replace(',', ''))
        except ValueError:
            pass
        
        # Check for boolean
        if value.lower() in ['true', 'yes', 'y', '1']:
            return True
        if value.lower() in ['false', 'no', 'n', '0']:
            return False
        
        # Return as string
        return value
