"""JSON fragment extraction utilities."""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from core import ExtractedRecord

from .base import BaseExtractor


class JSONExtractor(BaseExtractor):
    """Extractor for JSON fragments and code blocks."""

    def extract(self, content: str) -> List[ExtractedRecord]:
        """Extract JSON fragments from content and return as ExtractedRecords.
        
        Args:
            content: Raw text content potentially containing JSON fragments
            
        Returns:
            List of ExtractedRecord objects for each valid JSON fragment found
        """
        fragments = extract_json_fragments(content)
        records = []
        
        for fragment in fragments:
            parsed_data = parse_json_string(fragment["raw"])
            
            if parsed_data is not None:
                # Successfully parsed JSON - create ExtractedRecord
                record = ExtractedRecord(
                    data=parsed_data,
                    source_type="json",
                    confidence=1.0
                )
                records.append(record)
            else:
                # Failed to parse - store raw string with lower confidence
                record = ExtractedRecord(
                    data={
                        "_raw": fragment["raw"],
                        "_parse_error": True,
                        "chunk_id": fragment["chunk_id"],
                        "start": fragment["start"],
                        "end": fragment["end"]
                    },
                    source_type="json",
                    confidence=0.5
                )
                records.append(record)
        
        return records


def extract_json_fragments(text: str) -> List[Dict[str, Any]]:
    """Find and parse JSON blobs within text using bracket-stack scanning.
    
    Uses a conservative approach scanning for balanced {...} regions.
    
    Args:
        text: Raw text potentially containing JSON fragments
        
    Returns:
        List of dicts with keys: raw, start, end, chunk_id
    """
    fragments = []
    i = 0
    chunk_counter = 1
    
    while i < len(text):
        # Look for opening brace
        if text[i] == '{':
            start_idx = i
            stack = ['{']
            i += 1
            in_string = False
            escape_next = False
            
            # Scan for balanced closing brace
            while i < len(text) and stack:
                char = text[i]
                
                # Handle escape sequences in strings
                if escape_next:
                    escape_next = False
                    i += 1
                    continue
                
                if char == '\\':
                    escape_next = True
                    i += 1
                    continue
                
                # Handle string boundaries
                if char == '"':
                    in_string = not in_string
                    i += 1
                    continue
                
                # Only process braces outside of strings
                if not in_string:
                    if char == '{':
                        stack.append('{')
                    elif char == '}':
                        stack.pop()
                
                i += 1
            
            # If stack is empty, we found a balanced JSON candidate
            if not stack and i > start_idx:
                end_idx = i
                raw_json = text[start_idx:end_idx]
                
                fragments.append({
                    "raw": raw_json,
                    "start": start_idx,
                    "end": end_idx,
                    "chunk_id": f"json_{chunk_counter}"
                })
                chunk_counter += 1
        else:
            i += 1
    
    return fragments


def find_json_patterns(text: str) -> List[str]:
    """Return candidate JSON strings from raw text.
    
    Uses conservative bracket scanning to avoid false positives.
    
    Args:
        text: Raw text potentially containing JSON fragments
        
    Returns:
        List of raw JSON candidate strings
    """
    fragments = extract_json_fragments(text)
    return [frag["raw"] for frag in fragments]


def parse_json_string(json_str: str) -> Optional[Dict[str, Any]]:
    """Safely parse a JSON string with fallback fixes.
    
    Attempts to parse JSON with common fixes:
    - Remove trailing commas before closing braces/brackets
    - Replace single quotes with double quotes (if no double quotes present)
    
    Args:
        json_str: String potentially containing valid JSON
        
    Returns:
        Parsed dictionary if successful, None otherwise
    """
    # First attempt: parse as-is
    try:
        result = json.loads(json_str)
        if isinstance(result, dict):
            return result
        # If result is not a dict (e.g., list, string), wrap it
        return {"_value": result}
    except (json.JSONDecodeError, ValueError):
        pass
    
    # Second attempt: remove trailing commas
    try:
        fixed = re.sub(r',(\s*[}\]])', r'\1', json_str)
        result = json.loads(fixed)
        if isinstance(result, dict):
            return result
        return {"_value": result}
    except (json.JSONDecodeError, ValueError):
        pass
    
    # Third attempt: replace single quotes with double quotes
    # Only if there are no existing double quotes (to avoid breaking strings)
    if '"' not in json_str and "'" in json_str:
        try:
            fixed = json_str.replace("'", '"')
            result = json.loads(fixed)
            if isinstance(result, dict):
                return result
            return {"_value": result}
        except (json.JSONDecodeError, ValueError):
            pass
    
    # Fourth attempt: combine both fixes
    if "'" in json_str:
        try:
            fixed = json_str.replace("'", '"')
            fixed = re.sub(r',(\s*[}\]])', r'\1', fixed)
            result = json.loads(fixed)
            if isinstance(result, dict):
                return result
            return {"_value": result}
        except (json.JSONDecodeError, ValueError):
            pass
    
    # All attempts failed
    return None
