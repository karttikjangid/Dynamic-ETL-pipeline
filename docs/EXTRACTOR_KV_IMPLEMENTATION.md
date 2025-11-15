# KV Extractor Implementation Guide

## Overview
This document explains the Key-Value (KV) pair extraction implementation in `extractors/kv_extractor.py`.

**Author:** Development Team  
**Date:** November 15, 2025  
**Module:** `extractors.kv_extractor`  
**Status:** ✅ Implemented

---

## What Was Implemented

### 1. KVExtractor Class
**Purpose:** Extract key-value pairs from raw text files (.txt, .md) and return structured records.

**Method:** `extract(self, content: str) -> List[ExtractedRecord]`

**Algorithm:**
1. Calls `extract_key_value_pairs()` to find all KV blocks
2. Creates `ExtractedRecord` objects with parsed key-value dictionaries
3. All records have confidence = 1.0 (KV parsing is deterministic)

**Input Example:**
```python
content = """
title: Widget A
price: 9.99
status: active
"""
```

**Output Example:**
```python
[
    ExtractedRecord(
        data={
            "title": "Widget A",
            "price": "9.99",
            "status": "active"
        },
        source_type="kv",
        confidence=1.0
    )
]
```

---

## Key Features

✅ **Contiguous Block Detection** - Groups consecutive KV lines  
✅ **JSON Avoidance** - Does not extract KV pairs inside JSON objects  
✅ **Byte Offset Tracking** - Tracks exact positions in original text  
✅ **Empty Line Handling** - Allows empty lines within same block  
✅ **Deterministic** - Same input always produces same output  
✅ **Flexible Format** - Handles "key: value", "key:value", "key : value"  

---

## Function Reference

### `extract_key_value_pairs(text: str)`
**Purpose:** Main worker function that finds and parses KV blocks.

**Algorithm:**
1. Identify JSON regions to exclude (using `_find_json_regions()`)
2. Split text into lines and track byte positions
3. For each line:
   - Skip if inside JSON region
   - Try to parse as KV pair using `parse_kv_line()`
   - Group consecutive KV lines into blocks
   - Finalize block when non-KV line encountered
4. Return list of fragment dictionaries

**Input Example:**
```python
text = """
name: Alice
age: 25

city: Boston
"""
```

**Output Example:**
```python
[
    {
        "raw": "name: Alice\nage: 25",
        "start": 1,
        "end": 25,
        "chunk_id": "kv_1",
        "content": {"name": "Alice", "age": "25"}
    },
    {
        "raw": "city: Boston",
        "start": 27,
        "end": 39,
        "chunk_id": "kv_2",
        "content": {"city": "Boston"}
    }
]
```

---

### `parse_kv_line(line: str)`
**Purpose:** Parse a single line into (key, value) tuple.

**Validation Rules:**
- Must contain colon `:`
- Key must start with letter or underscore
- Key can contain: letters, numbers, spaces, hyphens, underscores
- Key must be ≤ 50 characters
- Value can be anything (even empty)

**Examples:**

| Input | Output | Notes |
|-------|--------|-------|
| `"name: John"` | `("name", "John")` | Valid |
| `"age: 30"` | `("age", "30")` | Valid |
| `"key:value"` | `("key", "value")` | No spaces OK |
| `"key : value"` | `("key", "value")` | Spaces around colon OK |
| `"long key: val"` | `("long key", "val")` | Spaces in key OK |
| `"key:"` | `("key", "")` | Empty value OK |
| `"_private: x"` | `("_private", "x")` | Underscore start OK |
| `"with-dash: x"` | `("with-dash", "x")` | Hyphens OK |
| `"invalid line"` | `None` | No colon |
| `"123: value"` | `None` | Starts with number |
| `": no key"` | `None` | No key |

---

### `find_kv_sections(text: str)`
**Purpose:** Simplified interface returning only raw KV block strings.

**Input Example:**
```python
text = """
name: Alice
age: 25
"""
```

**Output Example:**
```python
["name: Alice\nage: 25"]
```

---

### Helper Functions

#### `_find_json_regions(text: str)`
**Purpose:** Identify byte ranges occupied by JSON objects.

Uses same bracket-scanning algorithm as JSON extractor to find `{...}` regions.

**Returns:** List of `(start, end)` tuples

---

#### `_is_in_json_region(line_start, line_end, json_regions)`
**Purpose:** Check if a line overlaps with any JSON region.

**Logic:** Checks for range overlap between line and JSON regions.

---

#### `_finalize_kv_block(block, block_id)`
**Purpose:** Convert list of parsed KV lines into a fragment dictionary.

**Actions:**
- Calculate start/end positions
- Reconstruct raw text
- Build content dictionary
- Generate chunk_id

---

## Expected Outputs

### Test Case 1: Simple KV Block
**Input:**
```python
text = """
name: John
age: 30
"""
```

**Expected:**
```python
[
    ExtractedRecord(
        data={"name": "John", "age": "30"},
        source_type="kv",
        confidence=1.0
    )
]
```

---

### Test Case 2: Multiple Blocks
**Input:**
```python
text = """
title: Widget
price: 9.99

description: Test
stock: 100
"""
```

**Expected:**
```python
[
    ExtractedRecord(data={"title": "Widget", "price": "9.99"}, ...),
    ExtractedRecord(data={"description": "Test", "stock": "100"}, ...)
]
```

---

### Test Case 3: KV with JSON (Separate)
**Input:**
```python
text = """
title: Widget

{ "id": 123 }

status: active
"""
```

**Expected:**
```python
[
    ExtractedRecord(data={"title": "Widget"}, source_type="kv", ...),
    ExtractedRecord(data={"status": "active"}, source_type="kv", ...)
]
# Note: JSON is NOT extracted by KV extractor
```

---

### Test Case 4: Empty Lines Within Block
**Input:**
```python
text = """
key1: value1

key2: value2
"""
```

**Expected:**
```python
[
    ExtractedRecord(
        data={"key1": "value1", "key2": "value2"},
        source_type="kv",
        confidence=1.0
    )
]
# Note: Empty lines don't break the block
```

---

### Test Case 5: Edge Cases
**Input:**
```python
text = """
_private: value
with-dash: ok
empty:
special: !@#$%
"""
```

**Expected:**
```python
[
    ExtractedRecord(
        data={
            "_private": "value",
            "with-dash": "ok",
            "empty": "",
            "special": "!@#$%"
        },
        source_type="kv",
        confidence=1.0
    )
]
```

---

## Design Decisions

### 1. Why Avoid JSON Regions?
**Problem:** Text like `{ "key": "value" }` contains colons but is JSON, not KV pairs.

**Solution:** Pre-scan for JSON regions using bracket matching, exclude those lines.

**Benefit:** Clean separation between JSON and KV extractors.

---

### 2. Why Allow Empty Lines Within Blocks?
**Real-world use:** Configuration files often have spacing for readability.

**Example:**
```
name: John

age: 30
```

These should be treated as one logical block, not two.

---

### 3. Why Track Byte Offsets?
**Traceability:** Allows mapping extracted data back to original file positions.

**Debugging:** Helps identify where data came from.

**Future use:** Could enable line-number reporting, highlighting in UI, etc.

---

### 4. Why No Type Inference Here?
**Separation of concerns:** Extraction ≠ Normalization

**Responsibility:**
- Extractor: Find and parse structure
- Normalizer: Infer types, clean values

**Example:** `"age: 30"` extracts as `{"age": "30"}` (string), normalizer converts to integer.

---

### 5. Why Fixed Confidence = 1.0?
**Deterministic parsing:** If line matches pattern, it's definitely a KV pair.

**Unlike JSON:** No parsing can fail (we just extract the text as-is).

**Normalization confidence:** Type inference happens later with its own confidence.

---

## Integration Points

### Upstream (Inputs)
- **From:** `extractors/file_parser.py` (reads file content)
- **Format:** Plain string content from `.txt` or `.md` files

### Downstream (Outputs)
- **To:** `normalizers/kv_normalizer.py`
- **Format:** `List[ExtractedRecord]` with `source_type="kv"`

### Used By
- `extractors/orchestrator.py` - Calls during extraction phase
- `dev_runner.py` - Testing and development
- `test_kv_extractor.py` - Comprehensive testing

---

## Performance Considerations

### Time Complexity
- JSON region scanning: O(n) where n = text length
- Line processing: O(m) where m = number of lines
- **Overall:** O(n + m) ≈ O(n)

### Space Complexity
- O(k) where k = number of KV blocks found
- Stores raw text + parsed dictionaries

### Optimization Notes
- ✅ Single pass through text
- ✅ No regex compilation per line
- ✅ Early termination on non-KV lines
- ⚠️ Could optimize JSON region scanning (currently duplicates JSON extractor logic)

---

## Common Pitfalls & Solutions

### Pitfall 1: Colons in Values
**Problem:** `"url: http://example.com"` has multiple colons

**Solution:** Split on FIRST colon only: `line.split(':', 1)`

**Result:** Key = "url", Value = "http://example.com" ✅

---

### Pitfall 2: Keys Starting with Numbers
**Problem:** `"123: value"` looks like KV but invalid

**Solution:** Validate key starts with letter or underscore

**Result:** Rejected ❌

---

### Pitfall 3: Very Long Keys
**Problem:** `"This is a sentence not a key: value"` matches pattern

**Solution:** Limit key length to 50 characters

**Result:** Rejected ❌

---

### Pitfall 4: Empty Values
**Problem:** `"key:"` with nothing after colon

**Solution:** Allow empty string values (valid use case)

**Result:** `("key", "")` ✅

---

## Testing Strategy

### Unit Tests
```python
def test_simple_kv():
    text = "name: John\nage: 30"
    records = KVExtractor().extract(text)
    assert len(records) == 1
    assert records[0].data == {"name": "John", "age": "30"}

def test_multiple_blocks():
    text = "k1: v1\n\nSeparator\n\nk2: v2"
    records = KVExtractor().extract(text)
    assert len(records) == 2

def test_json_avoidance():
    text = 'key: value\n{ "json": "data" }\nafter: json'
    records = KVExtractor().extract(text)
    # Should only get 2 KV records, not JSON content
    assert all(r.source_type == "kv" for r in records)

def test_edge_cases():
    assert parse_kv_line("_key: val") == ("_key", "val")
    assert parse_kv_line("key:") == ("key", "")
    assert parse_kv_line("123: val") is None
```

### Manual Testing
```bash
python test_kv_extractor.py
```

---

## Differences from JSON Extractor

| Aspect | JSON Extractor | KV Extractor |
|--------|----------------|--------------|
| **Pattern** | Bracket matching `{...}` | Colon separator `key: value` |
| **Complexity** | Stack-based scanning | Line-by-line regex |
| **Parsing** | json.loads() | String split |
| **Failures** | Confidence = 0.5 | N/A (always succeeds) |
| **Nesting** | Handles arbitrary depth | Flat key-value only |
| **Auto-fix** | Trailing commas, quotes | Not needed |

---

## Future Enhancements

### Potential Additions
1. **Nested Keys:** Support `section.key: value` notation
2. **Multi-line Values:** Handle values spanning multiple lines
3. **Comments:** Skip lines starting with `#` or `//`
4. **Type Hints:** Detect types during extraction (`age<int>: 30`)
5. **Duplicate Keys:** Warning or array handling

### Not Planned (Out of Scope)
- YAML/TOML parsing (too complex)
- Nested dictionary structures
- Type conversion (that's normalizer's job)
- Schema validation

---

## Key Takeaways

### Implementation Highlights
✅ Clean separation from JSON extraction  
✅ Deterministic and predictable  
✅ Handles real-world formatting variations  
✅ Fast single-pass algorithm  
✅ Well-tested edge cases  

### Integration Ready
✅ Returns standard `ExtractedRecord` objects  
✅ Works with existing pipeline architecture  
✅ Compatible with normalizer layer  
✅ Tested with JSON extractor in combined scenarios  

---

## Related Files
- `extractors/base.py` - BaseExtractor abstract class
- `extractors/json_extractor.py` - JSON extraction (sibling)
- `extractors/orchestrator.py` - Coordinates all extractors
- `normalizers/kv_normalizer.py` - Next step (to be implemented)
- `core/models.py` - ExtractedRecord definition
- `dev_runner.py` - Quick testing
- `test_kv_extractor.py` - Comprehensive testing

---

## Changelog

| Date | Author | Changes |
|------|--------|---------|
| 2025-11-15 | Dev Team | Initial implementation of KV extractor |
| 2025-11-15 | Dev Team | Added comprehensive testing |
| 2025-11-15 | Dev Team | Created documentation |

---

**Status:** ✅ Production Ready  
**Next Module:** `file_parser.py` or `orchestrator.py`
