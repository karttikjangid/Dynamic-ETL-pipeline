"""YAML/front-matter extractor for Tier-B pipeline."""

import re
from typing import Any, Dict, List

import yaml

from core.models import ExtractedRecord
from extractors.base import BaseExtractor
from utils.logger import get_logger

logger = get_logger(__name__)


class YAMLExtractor(BaseExtractor):
    """Extracts YAML blocks and front-matter from text content."""

    def extract(self, content: str) -> List[ExtractedRecord]:
        """Extract all YAML blocks from content.
        
        Args:
            content: Raw text content potentially containing YAML
            
        Returns:
            List of ExtractedRecord objects with YAML data
        """
        yaml_blocks = extract_yaml_blocks(content)
        records = []
        
        for idx, yaml_data in enumerate(yaml_blocks):
            record = ExtractedRecord(
                data=yaml_data["data"],
                source_type="yaml_block",
                confidence=yaml_data["confidence"],
                metadata={
                    "yaml_id": yaml_data["yaml_id"],
                    "offset_start": yaml_data["offset_start"],
                    "offset_end": yaml_data["offset_end"],
                    "block_type": yaml_data["block_type"]
                }
            )
            records.append(record)
            
        logger.info(f"Extracted {len(records)} YAML block(s)")
        return records


def extract_yaml_blocks(text: str) -> List[Dict[str, Any]]:
    """Extract YAML blocks including front-matter.
    
    Args:
        text: Raw text potentially containing YAML blocks
        
    Returns:
        List of dicts containing parsed YAML data and metadata
    """
    results = []
    yaml_id = 0
    
    # Pattern 1: Front-matter (--- at start, --- at end)
    frontmatter_pattern = r'^---\s*\n(.*?)\n---\s*\n'
    frontmatter_matches = re.finditer(frontmatter_pattern, text, re.MULTILINE | re.DOTALL)
    
    for match in frontmatter_matches:
        yaml_content = match.group(1)
        try:
            data = yaml.safe_load(yaml_content)
            if data and isinstance(data, dict):
                yaml_id += 1
                results.append({
                    "yaml_id": f"yaml_{yaml_id}",
                    "data": data,
                    "offset_start": match.start(),
                    "offset_end": match.end(),
                    "block_type": "frontmatter",
                    "confidence": 0.95
                })
                logger.debug(f"Extracted front-matter YAML at offset {match.start()}")
        except yaml.YAMLError as e:
            logger.warning(f"Failed to parse front-matter YAML: {e}")
    
    # Pattern 2: Inline YAML blocks (with clear markers or indentation patterns)
    # Look for sections with consistent key: value patterns
    yaml_block_pattern = r'\n((?:[a-zA-Z_][a-zA-Z0-9_]*:\s*.+\n(?:\s+.+\n)*)+)'
    yaml_block_matches = re.finditer(yaml_block_pattern, text, re.MULTILINE)
    
    for match in yaml_block_matches:
        # Avoid overlapping with already extracted front-matter
        if any(r["offset_start"] <= match.start() < r["offset_end"] for r in results):
            continue
            
        yaml_content = match.group(1)
        
        # Only try to parse if it looks like YAML (has colons and proper indentation)
        if yaml_content.count(":") >= 2:
            try:
                data = yaml.safe_load(yaml_content)
                if data and isinstance(data, dict):
                    yaml_id += 1
                    results.append({
                        "yaml_id": f"yaml_{yaml_id}",
                        "data": data,
                        "offset_start": match.start(),
                        "offset_end": match.end(),
                        "block_type": "inline",
                        "confidence": 0.85
                    })
                    logger.debug(f"Extracted inline YAML at offset {match.start()}")
            except yaml.YAMLError:
                # Not valid YAML, skip
                pass
    
    return results
