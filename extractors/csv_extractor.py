"""CSV block extractor for Tier-B pipeline."""

import csv
import io
import re
from typing import Any, Dict, List

from core.models import ExtractedRecord
from extractors.base import BaseExtractor
from utils.logger import get_logger

logger = get_logger(__name__)


class CSVExtractor(BaseExtractor):
    """Extracts CSV-like blocks from text content."""

    def extract(self, content: str) -> List[ExtractedRecord]:
        """Extract all CSV blocks from content.
        
        Args:
            content: Raw text content potentially containing CSV blocks
            
        Returns:
            List of ExtractedRecord objects with CSV data
        """
        csv_blocks = extract_csv_blocks(content)
        records = []
        
        for idx, csv_data in enumerate(csv_blocks):
            record = ExtractedRecord(
                data=csv_data["rows"],
                source_type="csv_block",
                confidence=csv_data["confidence"],
                metadata={
                    "csv_id": csv_data["csv_id"],
                    "offset_start": csv_data["offset_start"],
                    "offset_end": csv_data["offset_end"],
                    "headers": csv_data["headers"],
                    "row_count": len(csv_data["rows"]),
                    "column_count": len(csv_data["headers"]) if csv_data["headers"] else 0,
                    "delimiter": csv_data["delimiter"]
                }
            )
            records.append(record)
            
        logger.info(f"Extracted {len(records)} CSV block(s)")
        return records


def extract_csv_blocks(text: str) -> List[Dict[str, Any]]:
    """Extract CSV-like blocks from text with heuristic detection.
    
    Args:
        text: Raw text potentially containing CSV blocks
        
    Returns:
        List of dicts containing CSV data, headers, and metadata
    """
    results = []
    lines = text.split("\n")
    
    csv_id = 0
    i = 0
    in_json_block = False
    in_yaml_block = False
    
    while i < len(lines):
        line = lines[i].strip()
        
        # Track JSON blocks
        if line.startswith("{"):
            in_json_block = True
        elif line.startswith("}"):
            in_json_block = False
            i += 1
            continue
        
        # Track YAML front-matter
        if line == "---":
            in_yaml_block = not in_yaml_block
            i += 1
            continue
        
        # Skip if inside JSON or YAML block
        if in_json_block or in_yaml_block:
            i += 1
            continue
        
        # Skip empty lines
        if not line:
            i += 1
            continue
        
        # Skip lines that are clearly not CSV
        if _is_likely_not_csv(line):
            i += 1
            continue
        
        # Check if line looks like CSV (contains commas or tabs)
        if "," in line or "\t" in line:
            # Detect delimiter
            delimiter = detect_delimiter(line)
            
            # Try to parse as CSV block
            csv_block, rows_consumed = try_parse_csv_block(
                lines[i:], delimiter
            )
            
            # Require at least 3 rows (header + 2 data rows) to be confident it's CSV
            if csv_block and len(csv_block) >= 3:  # At least header + 2 rows
                csv_id += 1
                
                # Calculate offsets
                offset_start = sum(len(lines[j]) + 1 for j in range(i))  # +1 for newline
                offset_end = sum(len(lines[j]) + 1 for j in range(i + rows_consumed))
                
                # First row is header
                headers = csv_block[0]
                rows = []
                
                for row_values in csv_block[1:]:
                    if len(row_values) == len(headers):
                        row_dict = dict(zip(headers, row_values))
                    else:
                        # Handle mismatched columns
                        row_dict = {}
                        for idx, val in enumerate(row_values):
                            key = headers[idx] if idx < len(headers) else f"col_{idx}"
                            row_dict[key] = val
                    rows.append(row_dict)
                
                # Calculate confidence based on consistency
                confidence = calculate_csv_confidence(csv_block, delimiter)
                
                results.append({
                    "csv_id": f"csv_block_{csv_id}",
                    "headers": headers,
                    "rows": rows,
                    "offset_start": offset_start,
                    "offset_end": offset_end,
                    "delimiter": delimiter,
                    "confidence": confidence
                })
                
                logger.debug(f"Extracted CSV block with {len(rows)} rows at line {i}")
                i += rows_consumed
            else:
                i += 1
        else:
            i += 1
    
    return results


def _is_likely_not_csv(line: str) -> bool:
    """Check if line is likely NOT CSV data.
    
    Args:
        line: Line to check
        
    Returns:
        True if line is likely not CSV
    """
    # Skip comment lines
    if line.startswith("#") or line.startswith("//") or line.startswith("---"):
        return True
    
    # Skip JSON/YAML indicators
    if line.startswith("{") or line.startswith("[") or line.startswith("}"):
        return True
    
    # Skip lines with JSON-like key:value without commas (KV pairs)
    if ":" in line and "," not in line and "\t" not in line:
        return True
    
    return False


def detect_delimiter(line: str) -> str:
    """Detect the most likely delimiter in a CSV line.
    
    Args:
        line: A single line of CSV text
        
    Returns:
        Detected delimiter character
    """
    # Count potential delimiters
    comma_count = line.count(",")
    tab_count = line.count("\t")
    pipe_count = line.count("|")
    semicolon_count = line.count(";")
    
    # Return most common delimiter
    counts = [
        (comma_count, ","),
        (tab_count, "\t"),
        (pipe_count, "|"),
        (semicolon_count, ";")
    ]
    counts.sort(reverse=True)
    
    return counts[0][1] if counts[0][0] > 0 else ","


def try_parse_csv_block(lines: List[str], delimiter: str) -> tuple[List[List[str]], int]:
    """Try to parse consecutive lines as a CSV block.
    
    Args:
        lines: List of lines starting from potential CSV start
        delimiter: Delimiter character to use
        
    Returns:
        Tuple of (parsed rows, number of lines consumed)
    """
    rows = []
    lines_consumed = 0
    expected_cols = None
    
    for line in lines:
        line = line.strip()
        
        # Stop at empty line or line without delimiter
        if not line or delimiter not in line:
            break
        
        try:
            # Parse line as CSV
            reader = csv.reader(io.StringIO(line), delimiter=delimiter)
            row = next(reader)
            row = [cell.strip() for cell in row]
            
            # Check column consistency
            if expected_cols is None:
                expected_cols = len(row)
            
            # Allow some flexibility in column count
            if abs(len(row) - expected_cols) <= 1:  # Within 1 column difference
                rows.append(row)
                lines_consumed += 1
            else:
                # Column count mismatch, stop parsing
                break
                
        except Exception as e:
            logger.debug(f"Failed to parse CSV line: {line[:50]}... Error: {e}")
            break
    
    return rows, lines_consumed


def calculate_csv_confidence(rows: List[List[str]], delimiter: str) -> float:
    """Calculate confidence score for a CSV block.
    
    Args:
        rows: Parsed CSV rows
        delimiter: Delimiter used
        
    Returns:
        Confidence score between 0.0 and 1.0
    """
    if len(rows) < 2:
        return 0.5
    
    confidence = 0.7  # Base confidence
    
    # Boost confidence for consistent column counts
    col_counts = [len(row) for row in rows]
    if len(set(col_counts)) == 1:  # All rows have same column count
        confidence += 0.15
    
    # Boost confidence for common CSV delimiters
    if delimiter in [",", "\t"]:
        confidence += 0.1
    
    # Cap at 0.95
    return min(confidence, 0.95)
