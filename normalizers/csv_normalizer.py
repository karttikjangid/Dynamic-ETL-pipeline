"""CSV normalizer for Tier-B pipeline."""

from typing import Any, Dict, List

from core.models import NormalizedRecord
from normalizers.base import BaseNormalizer
from utils.logger import get_logger

logger = get_logger(__name__)


class CSVNormalizer(BaseNormalizer):
    """Normalizes CSV data extracted from documents."""

    def normalize(self, data: Any, metadata: Dict[str, Any]) -> List[NormalizedRecord]:
        """Normalize CSV rows into standardized records.
        
        Args:
            data: List of row dictionaries from CSV block
            metadata: Metadata from extraction including csv_id, headers, etc.
            
        Returns:
            List of NormalizedRecord objects
        """
        if not isinstance(data, list):
            logger.warning(f"Expected list for CSV data, got {type(data)}")
            return []
        
        normalized_records = []
        
        for idx, row in enumerate(data):
            if not isinstance(row, dict):
                logger.warning(f"Row {idx} is not a dict, skipping")
                continue
            
            # Standardize keys and infer types
            normalized_data = {}
            for key, value in row.items():
                normalized_key = self._standardize_key(key)
                normalized_value = self._infer_type(value)
                normalized_data[normalized_key] = normalized_value
            
            # Create normalized record
            record = NormalizedRecord(
                data=normalized_data,
                source_type="csv_block",
                extraction_confidence=metadata.get("confidence", 0.9),
                provenance={
                    "csv_id": metadata.get("csv_id"),
                    "row_index": idx,
                    "offset_start": metadata.get("offset_start"),
                    "offset_end": metadata.get("offset_end"),
                    "headers": metadata.get("headers", []),
                    "delimiter": metadata.get("delimiter", ",")
                }
            )
            normalized_records.append(record)
        
        logger.info(f"Normalized {len(normalized_records)} CSV row(s)")
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
            value: String value from CSV cell
            
        Returns:
            Value cast to appropriate type
        """
        if not isinstance(value, str):
            return value
        
        value = value.strip()
        
        if not value or value.lower() in ['null', 'none', 'n/a', 'na']:
            return None
        
        # Try integer
        try:
            if '.' not in value and ',' not in value:
                return int(value)
        except ValueError:
            pass
        
        # Try float
        try:
            # Handle both comma and dot as decimal separator
            clean_value = value.replace(',', '.')
            if clean_value.count('.') == 1:
                return float(clean_value)
        except ValueError:
            pass
        
        # Check for boolean
        if value.lower() in ['true', 'yes', 'y', '1']:
            return True
        if value.lower() in ['false', 'no', 'n', '0']:
            return False
        
        # Try to parse as date (basic ISO format check)
        if self._looks_like_date(value):
            # Keep as string for now, more advanced date parsing later
            return value
        
        # Return as string
        return value

    def _looks_like_date(self, value: str) -> bool:
        """Check if a value looks like a date string.
        
        Args:
            value: String to check
            
        Returns:
            True if value appears to be a date
        """
        import re
        # Basic patterns for common date formats
        date_patterns = [
            r'^\d{4}-\d{2}-\d{2}',  # ISO: 2025-11-10
            r'^\d{2}/\d{2}/\d{4}',  # US: 11/10/2025
            r'^\d{2}-\d{2}-\d{4}',  # EU: 10-11-2025
        ]
        return any(re.match(pattern, value) for pattern in date_patterns)
