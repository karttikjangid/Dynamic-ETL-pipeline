# JSON Extractor Implementation Guide

## Overview
This document explains the JSON fragment extraction implementation in `extractors/json_extractor.py`.

**Author:** Development Team  
**Date:** November 15, 2025  
**Module:** `extractors.json_extractor`  
**Status:** ✅ Implemented

---

## What Was Implemented

### 1. JSONExtractor Class
**Purpose:** Extract JSON fragments from raw text files (.txt, .md) and return structured records.

**Method:** `extract(self, content: str) -> List[ExtractedRecord]`

**Algorithm:**
1. Calls `extract_json_fragments()` to find all JSON candidates
2. For each candidate, attempts to parse using `parse_json_string()`
3. Creates `ExtractedRecord` objects:
   - **Successful parse:** confidence = 1.0, data = parsed dict
   - **Failed parse:** confidence = 0.5, data = metadata with raw string

**Input Example:**
```python
content = """
Some text here
{ "id": "123", "name": "Sample Item", "details": {"color": "blue"} }
More text
"""
```

**Output Example:**
```python
[
    ExtractedRecord(
        data={
            "id": "123",
            "name": "Sample Item",
            "details": {"color": "blue"}
        },
        source_type="json",
        confidence=1.0
    )
]
```

---

### 2. extract_json_fragments() Function
**Purpose:** Find balanced JSON objects using bracket-stack scanning.

**Algorithm:**
- Scans character by character looking for `{`
- Uses a stack to track nested braces
- Handles:
  - String literals with proper quote tracking
  - Escape sequences (`\"`, `\\`)
  - Nested objects
- Returns when stack becomes empty (balanced)

**Why Stack-Based (Not Regex)?**
- ✅ Handles nested objects correctly
- ✅ Respects string boundaries
- ✅ Handles escape sequences
- ✅ More accurate for complex JSON
- ❌ Regex can't handle arbitrary nesting

**Input Example:**
```python
text = '{ "a": 1 } and { "b": { "c": 2 } }'
```

**Output Example:**
```python
[
    {
        "raw": '{ "a": 1 }',
        "start": 0,
        "end": 10,
        "chunk_id": "json_1"
    },
    {
        "raw": '{ "b": { "c": 2 } }',
        "start": 15,
        "end": 35,
        "chunk_id": "json_2"
    }
]
```

---

### 3. find_json_patterns() Function
**Purpose:** Simplified interface returning only raw JSON strings.

**Algorithm:**
- Wrapper around `extract_json_fragments()`
- Extracts just the "raw" field from each fragment

**Input Example:**
```python
text = '{ "id": 1 } text { "id": 2 }'
```

**Output Example:**
```python
['{ "id": 1 }', '{ "id": 2 }']
```

---

### 4. parse_json_string() Function
**Purpose:** Robust JSON parsing with automatic fixes for common issues.

**Algorithm - Progressive Fallback:**
1. **Attempt 1:** Parse as-is using `json.loads()`
2. **Attempt 2:** Remove trailing commas: `,}` → `}`
3. **Attempt 3:** Replace single quotes: `'` → `"`
4. **Attempt 4:** Combine both fixes
5. **Return None** if all attempts fail

**Special Handling:**
- Non-dict results (arrays, primitives) wrapped in `{"_value": ...}`
- Only replaces quotes if safe (no existing double quotes)

**Input/Output Examples:**

| Input | Output | Notes |
|-------|--------|-------|
| `'{"id": 1}'` | `{"id": 1}` | Valid JSON |
| `'{"id": 1,}'` | `{"id": 1}` | Trailing comma fixed |
| `"{'id': 1}"` | `{"id": 1}` | Single quotes fixed |
| `'[1, 2, 3]'` | `{"_value": [1, 2, 3]}` | Array wrapped |
| `'invalid'` | `None` | Unparseable |

---

## Expected Outputs

### Test Case 1: Simple JSON
**Input:**
```python
text = '{ "id": "123", "name": "Sample" }'
extractor = JSONExtractor()
records = extractor.extract(text)
```

**Expected Output:**
```python
[
    ExtractedRecord(
        data={"id": "123", "name": "Sample"},
        source_type="json",
        confidence=1.0
    )
]
```

---

### Test Case 2: Nested JSON
**Input:**
```python
text = '{ "user": {"id": 1, "profile": {"age": 30}} }'
```

**Expected Output:**
```python
[
    ExtractedRecord(
        data={
            "user": {
                "id": 1,
                "profile": {"age": 30}
            }
        },
        source_type="json",
        confidence=1.0
    )
]
```

---

### Test Case 3: Multiple JSON Fragments
**Input:**
```python
text = '''
First: { "id": 1 }
Second: { "id": 2 }
'''
```

**Expected Output:**
```python
[
    ExtractedRecord(data={"id": 1}, source_type="json", confidence=1.0),
    ExtractedRecord(data={"id": 2}, source_type="json", confidence=1.0)
]
```

---

### Test Case 4: JSON with Trailing Comma (Auto-Fixed)
**Input:**
```python
text = '{ "id": 1, "name": "test", }'
```

**Expected Output:**
```python
[
    ExtractedRecord(
        data={"id": 1, "name": "test"},
        source_type="json",
        confidence=1.0
    )
]
```

---

### Test Case 5: Malformed JSON (Failed Parse)
**Input:**
```python
text = '{ "id": 1, broken }'
```

**Expected Output:**
```python
[
    ExtractedRecord(
        data={
            "_raw": '{ "id": 1, broken }',
            "_parse_error": True,
            "chunk_id": "json_1",
            "start": 0,
            "end": 19
        },
        source_type="json",
        confidence=0.5
    )
]
```

---

### Test Case 6: JSON in Mixed Content
**Input:**
```python
text = '''
title: Widget A
price: 9.99

{ "id": "123", "name": "Sample Item", "details": {"color": "blue"} }

More text here
'''
```

**Expected Output:**
```python
[
    ExtractedRecord(
        data={
            "id": "123",
            "name": "Sample Item",
            "details": {"color": "blue"}
        },
        source_type="json",
        confidence=1.0
    )
]
```

---

## Design Decisions

### 1. Why Stack-Based Scanning?
- **Regex limitations:** Can't handle arbitrary nesting
- **Accuracy:** Properly handles strings, escapes, nesting
- **Performance:** O(n) single pass through text

### 2. Why Multiple Parse Attempts?
- **Real-world data:** Often has minor formatting issues
- **Robustness:** Increases extraction success rate
- **Conservative:** Only applies safe transformations

### 3. Why Store Failed Parses?
- **Debugging:** Helps identify problematic data
- **Traceability:** Preserves original positions
- **Lower confidence:** Signals downstream that verification needed

### 4. Why Wrap Non-Dict Results?
- **Consistency:** All ExtractedRecords have Dict data
- **Schema inference:** Works uniformly downstream
- **Preservation:** Original value accessible via `_value` key

---

## Integration Points

### Upstream (Inputs)
- **From:** `extractors/file_parser.py` (reads file content)
- **Format:** Plain string content from `.txt` or `.md` files

### Downstream (Outputs)
- **To:** `normalizers/json_normalizer.py`
- **Format:** `List[ExtractedRecord]` with `source_type="json"`

### Used By
- `extractors/orchestrator.py` - Calls during extraction phase
- `dev_runner.py` - Testing and development

---

## Testing Strategy

### Unit Tests (Recommended)
```python
def test_simple_json():
    text = '{"id": 1}'
    records = JSONExtractor().extract(text)
    assert len(records) == 1
    assert records[0].data == {"id": 1}
    assert records[0].confidence == 1.0

def test_nested_json():
    text = '{"a": {"b": {"c": 1}}}'
    records = JSONExtractor().extract(text)
    assert records[0].data["a"]["b"]["c"] == 1

def test_multiple_fragments():
    text = '{"id": 1} text {"id": 2}'
    records = JSONExtractor().extract(text)
    assert len(records) == 2

def test_trailing_comma_fix():
    text = '{"id": 1,}'
    records = JSONExtractor().extract(text)
    assert records[0].data == {"id": 1}

def test_malformed_json():
    text = '{invalid}'
    records = JSONExtractor().extract(text)
    assert records[0].confidence == 0.5
    assert "_parse_error" in records[0].data
```

### Manual Testing
```bash
python dev_runner.py
```

---

## Performance Considerations

### Time Complexity
- `extract_json_fragments()`: O(n) - single pass
- `parse_json_string()`: O(n) - json.loads is O(n)
- **Overall:** O(n) where n = input text length

### Space Complexity
- O(m) where m = number of JSON fragments found
- Stores raw strings + parsed data

### Optimization Opportunities
- ⚠️ Large files: Consider streaming/chunking
- ⚠️ Many fragments: Consider lazy evaluation
- ✅ Current approach fine for Tier-A (small-medium files)

---

## Common Pitfalls & Solutions

### Pitfall 1: Strings Containing Braces
**Problem:** `{"text": "hello {world}"}` might confuse naive parsers

**Solution:** Track `in_string` state, only count braces outside strings

### Pitfall 2: Escaped Quotes
**Problem:** `{"text": "say \"hi\""}` quote tracking breaks

**Solution:** Track `escape_next` flag for backslash handling

### Pitfall 3: Single Quotes in JSON
**Problem:** `{'id': 1}` is not valid JSON but common in Python

**Solution:** Fallback parser replaces `'` with `"` when safe

### Pitfall 4: Trailing Commas
**Problem:** `{"id": 1,}` invalid but common in JavaScript

**Solution:** Regex removes trailing commas before parse

---

## Future Enhancements

### Potential Additions
1. **JSON Arrays:** Currently focuses on objects `{...}`, could add `[...]`
2. **Code Block Extraction:** Parse markdown fenced code blocks
3. **Line Numbers:** Track line/column for better error reporting
4. **Validation:** JSON Schema validation if schema provided
5. **Streaming:** Handle very large files without loading fully

### Not Planned (Out of Scope for Tier-A)
- HTML table extraction
- CSV parsing
- XML/YAML conversion
- Schema reconciliation
- Natural language parsing

---

## Key Takeaways for Teammates

### When Working with This Module

✅ **Do:**
- Use `JSONExtractor().extract()` as the main entry point
- Check `confidence` scores on returned records
- Handle both successful and failed parses
- Use `dev_runner.py` for quick testing

❌ **Don't:**
- Modify the stack-based scanning logic without testing extensively
- Assume all extractions will have confidence 1.0
- Skip testing with nested/complex JSON
- Add dependencies outside Python stdlib

### Questions to Ask
1. Should we extract JSON arrays `[...]` in addition to objects?
2. How should we handle JSON fragments spanning multiple lines?
3. Should we add a maximum nesting depth limit?
4. What confidence threshold should normalizers use to filter records?

---

## Related Files
- `extractors/base.py` - BaseExtractor abstract class
- `extractors/kv_extractor.py` - Key-value extraction (to be implemented)
- `extractors/orchestrator.py` - Coordinates all extractors
- `core/models.py` - ExtractedRecord definition
- `dev_runner.py` - Manual testing script

---

## Changelog

| Date | Author | Changes |
|------|--------|---------|
| 2025-11-15 | Dev Team | Initial implementation of JSON extractor |
| 2025-11-15 | Dev Team | Added documentation and guidelines |

---

## Contact
For questions about this implementation, refer to:
- `guidelines.md` - Overall project architecture
- Code comments in `json_extractor.py`
- This documentation file
