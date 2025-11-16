"""Extraction orchestration helpers."""

from __future__ import annotations

from typing import Dict, List, Tuple

from core import ExtractedRecord
from utils.logger import get_logger

from .file_parser import parse_file
from .json_extractor import JSONExtractor
from .kv_extractor import KVExtractor
from .html_extractor import HTMLExtractor
from .csv_extractor import CSVExtractor
from .yaml_extractor import YAMLExtractor

logger = get_logger(__name__)


def extract_all_records(file_path: str) -> Tuple[List[ExtractedRecord], Dict[str, int]]:
    """Run all extractors against the file and return stats.
    
    Args:
        file_path: Path to the file to extract from
        
    Returns:
        Tuple of (all_records, extraction_stats)
    """
    # Parse the file to get text content
    text = parse_file(file_path)
    pdf_pages = _count_pdf_pages(text)
    
    # Initialize Tier-A extractors
    json_extractor = JSONExtractor()
    kv_extractor = KVExtractor()
    
    # Initialize Tier-B extractors
    html_extractor = HTMLExtractor()
    csv_extractor = CSVExtractor()
    yaml_extractor = YAMLExtractor()
    
    # Extract all fragments
    json_records = json_extractor.extract(text)
    kv_records = kv_extractor.extract(text)
    html_records = html_extractor.extract(text)
    csv_records = csv_extractor.extract(text)
    yaml_records = yaml_extractor.extract(text)
    
    # Combine records
    all_records = combine_extracted_records(
        json_records, kv_records, html_records, csv_records, yaml_records
    )
    
    # Build stats
    stats = {
        "json_fragments": len(json_records),
        "kv_pairs": len(kv_records),
        "html_tables": len(html_records),
        "csv_blocks": len(csv_records),
        "yaml_blocks": len(yaml_records),
        "total_records": len(all_records)
    }
    if pdf_pages:
        stats["pdf_pages"] = pdf_pages
    
    # Log stats
    log_extraction_stats(stats)
    
    return all_records, stats


def combine_extracted_records(
    json_records: List[ExtractedRecord],
    kv_records: List[ExtractedRecord],
    html_records: List[ExtractedRecord],
    csv_records: List[ExtractedRecord],
    yaml_records: List[ExtractedRecord],
) -> List[ExtractedRecord]:
    """Merge all extraction results preserving ordering metadata.
    
    Combines records from different extractors and sorts them by
    their position in the original text (if position metadata available).
    
    Args:
        json_records: Records from JSON extractor
        kv_records: Records from KV extractor
        html_records: Records from HTML extractor
        csv_records: Records from CSV extractor
        yaml_records: Records from YAML extractor
        
    Returns:
        Combined and sorted list of ExtractedRecord objects
    """
    # Combine all records
    all_records = (
        json_records + 
        kv_records + 
        html_records + 
        csv_records + 
        yaml_records
    )
    
    # Sort by offset if available in metadata
    def get_offset(record: ExtractedRecord) -> float:
        if record.metadata and "offset_start" in record.metadata:
            return record.metadata["offset_start"]
        return float('inf')  # Records without offset go to end
    
    all_records.sort(key=get_offset)
    
    return all_records


def log_extraction_stats(stats: Dict[str, int]) -> None:
    """Send extraction metrics to the shared logger.
    
    Args:
        stats: Dictionary containing extraction statistics
    """
    logger.info("Extraction complete:")
    logger.info(f"  JSON fragments: {stats.get('json_fragments', 0)}")
    logger.info(f"  KV pairs: {stats.get('kv_pairs', 0)}")
    logger.info(f"  HTML tables: {stats.get('html_tables', 0)}")
    logger.info(f"  CSV blocks: {stats.get('csv_blocks', 0)}")
    logger.info(f"  YAML blocks: {stats.get('yaml_blocks', 0)}")
    if "pdf_pages" in stats:
        logger.info(f"  PDF pages parsed: {stats.get('pdf_pages', 0)}")
    logger.info(f"  Total records: {stats.get('total_records', 0)}")


def _count_pdf_pages(text: str) -> int:
    """Return inferred PDF page count based on inserted page headers."""

    marker = "--- PAGE "
    occurrences = text.count(marker)
    return occurrences if occurrences > 0 else 0
