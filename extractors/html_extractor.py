"""HTML table extractor for Tier-B pipeline."""

from typing import Any, Dict, List

from bs4 import BeautifulSoup

from core.models import ExtractedRecord
from extractors.base import BaseExtractor
from utils.logger import get_logger

logger = get_logger(__name__)


class HTMLExtractor(BaseExtractor):
    """Extracts HTML tables from text content."""

    def extract(self, content: str) -> List[ExtractedRecord]:
        """Extract all HTML tables from content.
        
        Args:
            content: Raw text content potentially containing HTML
            
        Returns:
            List of ExtractedRecord objects with table data
        """
        tables = extract_html_tables(content)
        records = []
        
        for idx, table_data in enumerate(tables):
            record = ExtractedRecord(
                data=table_data["rows"],
                source_type="html_table",
                confidence=0.95,  # High confidence for well-formed tables
                metadata={
                    "table_id": table_data["table_id"],
                    "offset_start": table_data["offset_start"],
                    "offset_end": table_data["offset_end"],
                    "headers": table_data["headers"],
                    "row_count": len(table_data["rows"]),
                    "column_count": len(table_data["headers"]) if table_data["headers"] else 0
                }
            )
            records.append(record)
            
        logger.info(f"Extracted {len(records)} HTML table(s)")
        return records


def extract_html_tables(text: str) -> List[Dict[str, Any]]:
    """Extract HTML tables with metadata.
    
    Args:
        text: Raw text potentially containing HTML tables
        
    Returns:
        List of dicts containing table data, headers, and offset information
    """
    results = []
    
    # Find all <table> tags with their positions
    table_start_pos = 0
    table_id = 0
    
    while True:
        table_start_pos = text.find("<table", table_start_pos)
        if table_start_pos == -1:
            break
            
        # Find matching closing tag
        table_end_pos = text.find("</table>", table_start_pos)
        if table_end_pos == -1:
            logger.warning(f"Unclosed <table> tag at position {table_start_pos}")
            table_start_pos += 1
            continue
            
        table_end_pos += len("</table>")
        table_html = text[table_start_pos:table_end_pos]
        
        try:
            # Parse the table
            soup = BeautifulSoup(table_html, "html.parser")
            table = soup.find("table")
            
            if not table:
                table_start_pos = table_end_pos
                continue
            
            # Extract headers
            headers = []
            thead = table.find("thead")
            if thead:
                header_row = thead.find("tr")
                if header_row:
                    headers = [th.get_text(strip=True) for th in header_row.find_all(["th", "td"])]
            
            # If no thead, check first row
            if not headers:
                first_row = table.find("tr")
                if first_row:
                    # Check if first row contains <th> tags
                    ths = first_row.find_all("th")
                    if ths:
                        headers = [th.get_text(strip=True) for th in ths]
            
            # Extract rows
            rows = []
            tbody = table.find("tbody") or table
            for tr in tbody.find_all("tr"):
                # Skip header row if we already extracted it
                if tr.find("th") and headers:
                    continue
                    
                cells = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
                if cells:  # Only add non-empty rows
                    if headers and len(cells) == len(headers):
                        row_dict = dict(zip(headers, cells))
                    else:
                        # No headers or mismatch, use column indices
                        row_dict = {f"col_{i}": val for i, val in enumerate(cells)}
                    rows.append(row_dict)
            
            if rows:
                table_id += 1
                results.append({
                    "table_id": f"html_table_{table_id}",
                    "headers": headers,
                    "rows": rows,
                    "offset_start": table_start_pos,
                    "offset_end": table_end_pos
                })
                logger.debug(f"Extracted table with {len(rows)} rows at offset {table_start_pos}")
                
        except Exception as e:
            logger.warning(f"Failed to parse HTML table at position {table_start_pos}: {e}")
        
        table_start_pos = table_end_pos
    
    return results
