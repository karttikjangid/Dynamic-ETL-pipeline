"""Key-value extraction utilities."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Set, Tuple

from core import ExtractedRecord

from .base import BaseExtractor


class KVExtractor(BaseExtractor):
    """Extractor for structured key-value sections."""

    def extract(self, content: str) -> List[ExtractedRecord]:
        """Extract key-value blocks from text and return as ExtractedRecords.
        
        Args:
            content: Raw text content potentially containing key-value pairs
            
        Returns:
            List of ExtractedRecord objects for each KV block found
        """
        fragments = extract_key_value_pairs(content)
        records = []
        
        for fragment in fragments:
            # Create ExtractedRecord for each KV block
            metadata = {
                "chunk_id": fragment["chunk_id"],
                "offset_start": fragment["start"],
                "offset_end": fragment["end"],
            }
            record = ExtractedRecord(
                data=fragment["content"],
                source_type="kv",
                confidence=1.0,
                metadata=metadata
            )
            records.append(record)
        
        return records


def extract_key_value_pairs(text: str) -> List[Dict[str, Any]]:
    """Extract key-value blocks from text, avoiding JSON regions.
    
    Identifies contiguous blocks of "key: value" lines and returns them
    with metadata about their location in the original text.
    
    Args:
        text: Raw text potentially containing key-value pairs
        
    Returns:
        List of dicts with keys: raw, start, end, chunk_id, content
    """
    # Use extract_kv_fragments to get base fragments
    fragments = extract_kv_fragments(text)
    
    # Parse each fragment's content into key-value dictionary
    for fragment in fragments:
        raw = fragment["raw"]
        content = {}
        
        # Parse each line in the raw text
        for line in raw.split('\n'):
            parsed = parse_kv_line(line)
            if parsed:
                key, value = parsed
                # If duplicate keys exist, keep the last one (deterministic)
                content[key] = value
        
        # Add content to fragment
        fragment["content"] = content
    
    return fragments


def find_kv_sections(text: str) -> List[str]:
    """Locate sections likely containing key-value pairs.
    
    Returns just the raw text of each KV block found.
    
    Args:
        text: Raw text potentially containing key-value pairs
        
    Returns:
        List of raw KV block strings
    """
    fragments = extract_key_value_pairs(text)
    return [frag["raw"] for frag in fragments]


def parse_kv_line(line: str) -> Optional[Tuple[str, str]]:
    """Parse a line into a key/value tuple if possible.
    
    Matches patterns like:
    - "key: value"
    - "key : value"
    - "key:value"
    
    Key must start with a letter or underscore and can contain
    alphanumeric characters, underscores, hyphens, and spaces.
    
    Args:
        line: Single line of text to parse
        
    Returns:
        Tuple of (key, value) if valid KV pair, None otherwise
    """
    # Strip whitespace
    line = line.strip()
    
    # Empty line
    if not line:
        return None
    
    # Look for colon separator
    if ':' not in line:
        return None
    
    # Split on first colon
    parts = line.split(':', 1)
    if len(parts) != 2:
        return None
    
    key = parts[0].strip()
    value = parts[1].strip()
    
    # Validate key: must start with letter/underscore, can contain alphanumeric, spaces, hyphens, underscores
    # Must not be empty
    if not key:
        return None
    
    # Key should start with letter or underscore
    if not (key[0].isalpha() or key[0] == '_'):
        return None
    
    # Key should be reasonable length (not too long to be a sentence)
    if len(key) > 50:
        return None
    
    # Check if key looks like a valid identifier/label
    # Allow letters, numbers, spaces, underscores, hyphens
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_\s\-]*$', key):
        return None
    
    # Value should exist (even if empty string after colon)
    # We allow empty values like "key:"
    
    return (key, value)


def _find_json_regions(text: str) -> List[Tuple[int, int]]:
    """Find byte ranges occupied by JSON fragments in the text.
    
    Uses simplified bracket scanning to identify JSON object regions.
    
    Args:
        text: Raw text to scan
        
    Returns:
        List of (start, end) byte position tuples for JSON regions
    """
    regions = []
    i = 0
    
    while i < len(text):
        if text[i] == '{':
            start_idx = i
            stack = ['{']
            i += 1
            in_string = False
            escape_next = False
            
            while i < len(text) and stack:
                char = text[i]
                
                if escape_next:
                    escape_next = False
                    i += 1
                    continue
                
                if char == '\\':
                    escape_next = True
                    i += 1
                    continue
                
                if char == '"':
                    in_string = not in_string
                    i += 1
                    continue
                
                if not in_string:
                    if char == '{':
                        stack.append('{')
                    elif char == '}':
                        stack.pop()
                
                i += 1
            
            if not stack and i > start_idx:
                regions.append((start_idx, i))
        else:
            i += 1
    
    return regions


def _is_in_json_region(line_start: int, line_end: int, json_regions: List[Tuple[int, int]]) -> bool:
    """Check if a line overlaps with any JSON region.
    
    Args:
        line_start: Start byte position of line
        line_end: End byte position of line
        json_regions: List of (start, end) tuples for JSON regions
        
    Returns:
        True if line overlaps with any JSON region
    """
    for json_start, json_end in json_regions:
        # Check for any overlap
        if not (line_end < json_start or line_start >= json_end):
            return True
    return False


def extract_kv_fragments(text: str) -> List[Dict[str, Any]]:
    """Extract KV blocks of 'key: value' lines with offsets.
    
    Uses splitlines(keepends=True) and cumulative length-based offsets
    to precisely track byte positions. Groups consecutive KV lines into blocks.
    
    Args:
        text: Raw text potentially containing key-value pairs
        
    Returns:
        List of dicts with keys: raw, start, end, chunk_id
    """
    # First, identify JSON regions to exclude
    json_regions = _find_json_regions(text)
    
    # Split into lines while preserving line endings
    lines = text.splitlines(keepends=True)
    
    fragments = []
    current_block_lines = []
    current_block_start = 0
    block_counter = 1
    
    # Track cumulative byte offset
    offset = 0
    
    for line_with_ending in lines:
        line_start = offset
        line_end = offset + len(line_with_ending)
        
        # Get line without ending for parsing
        line = line_with_ending.rstrip('\r\n')
        
        # Check if this line is inside a JSON region
        if _is_in_json_region(line_start, line_end, json_regions):
            # Finalize current block if exists
            if current_block_lines:
                fragment = _finalize_kv_fragment(
                    current_block_lines, 
                    current_block_start, 
                    block_counter
                )
                if fragment:
                    fragments.append(fragment)
                    block_counter += 1
                current_block_lines = []
            
            # Move offset forward
            offset = line_end
            continue
        
        # Try to parse the line as key-value
        parsed = parse_kv_line(line)
        
        if parsed:
            # Valid KV line
            if not current_block_lines:
                # Starting a new block
                current_block_start = line_start
            
            current_block_lines.append({
                "line": line,
                "line_with_ending": line_with_ending,
                "start": line_start,
                "end": line_end,
                "parsed": parsed
            })
        else:
            # Not a KV line
            if line.strip() == "":
                # Empty line - continue (allows gaps within block)
                pass
            else:
                # Non-empty, non-KV line - finalize current block
                if current_block_lines:
                    fragment = _finalize_kv_fragment(
                        current_block_lines,
                        current_block_start,
                        block_counter
                    )
                    if fragment:
                        fragments.append(fragment)
                        block_counter += 1
                    current_block_lines = []
        
        # Move offset forward
        offset = line_end
    
    # Finalize any remaining block
    if current_block_lines:
        fragment = _finalize_kv_fragment(
            current_block_lines,
            current_block_start,
            block_counter
        )
        if fragment:
            fragments.append(fragment)
    
    return fragments


def _finalize_kv_fragment(
    block_lines: List[Dict[str, Any]], 
    block_start: int, 
    block_id: int
) -> Optional[Dict[str, Any]]:
    """Convert a list of KV line dicts into a fragment dict.
    
    Args:
        block_lines: List of line dictionaries with parsed KV data
        block_start: Start byte position of the block
        block_id: Block counter for chunk_id
        
    Returns:
        Fragment dict with raw, start, end, chunk_id
    """
    if not block_lines:
        return None
    
    # Calculate overall start/end positions
    start = block_lines[0]["start"]
    end = block_lines[-1]["end"]
    
    # Build raw text from original lines (with endings preserved)
    raw = ''.join(item["line_with_ending"] for item in block_lines)
    # Strip trailing newlines for cleaner raw text
    raw = raw.rstrip('\r\n')
    
    return {
        "raw": raw,
        "start": start,
        "end": end,
        "chunk_id": f"kv_{block_id}"
    }
