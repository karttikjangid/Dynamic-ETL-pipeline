# Quick Reference: JSON Extractor

## For Teammates Working on This Codebase

### What Was Done ✅

**Module:** `extractors/json_extractor.py`  
**Status:** Fully Implemented  
**Date:** November 15, 2025

---

## TL;DR (Too Long; Didn't Read)

**What it does:** Finds JSON objects `{...}` in text files and converts them to `ExtractedRecord` objects.

**How to use:**
```python
from extractors.json_extractor import JSONExtractor

extractor = JSONExtractor()
records = extractor.extract("{ \"id\": 1, \"name\": \"test\" }")
# Returns: [ExtractedRecord(data={'id': 1, 'name': 'test'}, source_type='json', confidence=1.0)]
```

**Key features:**
- Handles nested JSON
- Auto-fixes trailing commas and single quotes
- Returns confidence scores
- Preserves failed parses for debugging

---

## Quick Function Reference

### 1. `JSONExtractor().extract(content: str)`
**Main entry point** - Use this in your code!

```python
extractor = JSONExtractor()
records = extractor.extract(text)

for record in records:
    print(record.data)           # Parsed JSON as dict
    print(record.source_type)    # "json"
    print(record.confidence)     # 1.0 or 0.5
```

---

### 2. `extract_json_fragments(text: str)`
**Low-level function** - Finds JSON locations

```python
from extractors.json_extractor import extract_json_fragments

fragments = extract_json_fragments("{ \"a\": 1 } text { \"b\": 2 }")
# Returns: [
#   {"raw": '{ "a": 1 }', "start": 0, "end": 10, "chunk_id": "json_1"},
#   {"raw": '{ "b": 2 }', "start": 16, "end": 26, "chunk_id": "json_2"}
# ]
```

---

### 3. `find_json_patterns(text: str)`
**Simplified version** - Just returns raw strings

```python
from extractors.json_extractor import find_json_patterns

patterns = find_json_patterns("{ \"a\": 1 } and { \"b\": 2 }")
# Returns: ['{ "a": 1 }', '{ "b": 2 }']
```

---

### 4. `parse_json_string(json_str: str)`
**Parser with auto-fix** - Handles malformed JSON

```python
from extractors.json_extractor import parse_json_string

# Valid JSON
parse_json_string('{"id": 1}')          # → {"id": 1}

# Trailing comma (auto-fixed)
parse_json_string('{"id": 1,}')         # → {"id": 1}

# Single quotes (auto-fixed)
parse_json_string("{'id': 1}")          # → {"id": 1}

# Unparseable
parse_json_string('{invalid}')          # → None
```

---

## Output Format

### Success Case (confidence = 1.0)
```python
ExtractedRecord(
    data={
        "id": "123",
        "name": "Sample",
        "nested": {"key": "value"}
    },
    source_type="json",
    confidence=1.0
)
```

### Failure Case (confidence = 0.5)
```python
ExtractedRecord(
    data={
        "_raw": '{ broken json }',
        "_parse_error": True,
        "chunk_id": "json_1",
        "start": 0,
        "end": 16
    },
    source_type="json",
    confidence=0.5
)
```

---

## Testing Your Changes

### Quick Test
```bash
python dev_runner.py
```

### Unit Test Template
```python
def test_your_feature():
    from extractors.json_extractor import JSONExtractor
    
    extractor = JSONExtractor()
    text = '{"test": "data"}'
    records = extractor.extract(text)
    
    assert len(records) == 1
    assert records[0].data == {"test": "data"}
    assert records[0].confidence == 1.0
```

---

## Integration Points

### Where This Fits in the Pipeline

```
File Upload
    ↓
file_parser.py (reads file) ← YOU IMPLEMENT THIS NEXT
    ↓
json_extractor.py (extracts JSON) ← ✅ DONE
    ↓
json_normalizer.py (cleans data) ← TODO
    ↓
schema_generator.py (infers types) ← TODO
    ↓
MongoDB storage ← TODO
```

---

## Common Use Cases

### Use Case 1: Extract from File Content
```python
# After file_parser is implemented:
from extractors.file_parser import parse_file
from extractors.json_extractor import JSONExtractor

content = parse_file("data.txt")
extractor = JSONExtractor()
records = extractor.extract(content)
```

### Use Case 2: Filter by Confidence
```python
records = extractor.extract(text)
high_confidence = [r for r in records if r.confidence >= 0.8]
```

### Use Case 3: Extract Specific Fields
```python
records = extractor.extract(text)
for record in records:
    if record.confidence == 1.0:
        user_id = record.data.get("id")
        print(f"Found user: {user_id}")
```

---

## What to Implement Next

### Priority 1: Key-Value Extractor
**File:** `extractors/kv_extractor.py`  
**Similar to:** JSON extractor but for `key: value` pairs

### Priority 2: File Parser
**File:** `extractors/file_parser.py`  
**Purpose:** Read `.txt` and `.md` files, extract code blocks

### Priority 3: Orchestrator
**File:** `extractors/orchestrator.py`  
**Purpose:** Combine JSON + KV extraction results

---

## Design Decisions (Why We Did It This Way)

### Q: Why stack-based scanning instead of regex?
**A:** Regex can't handle nested objects like `{"a": {"b": {"c": 1}}}`

### Q: Why store failed parses?
**A:** Debugging & traceability. Downstream can decide what to do.

### Q: Why auto-fix trailing commas?
**A:** Real-world data often has minor issues. Makes system more robust.

### Q: Why confidence scores?
**A:** Lets downstream modules decide quality threshold.

---

## Gotchas & Common Mistakes

### ❌ Don't Do This
```python
# Don't call internal functions directly in production
fragments = extract_json_fragments(text)  # Use JSONExtractor().extract() instead
```

### ✅ Do This
```python
# Use the main class interface
extractor = JSONExtractor()
records = extractor.extract(text)
```

---

### ❌ Don't Assume All Confidence = 1.0
```python
# Bad: assumes all extractions succeed
data = records[0].data["id"]  # Might fail if parse failed
```

### ✅ Check Confidence First
```python
# Good: validate before using
if record.confidence >= 0.8:
    data = record.data.get("id", "unknown")
```

---

## FAQ

**Q: Can it handle JSON arrays `[...]`?**  
A: Not yet. Currently only extracts objects `{...}`. Future enhancement.

**Q: What about markdown code blocks?**  
A: Not implemented. That's for `file_parser.py` to extract first.

**Q: Maximum nesting depth?**  
A: No limit. Stack-based approach handles arbitrary nesting.

**Q: Thread-safe?**  
A: Yes. No shared state. Each `extract()` call is independent.

**Q: What if file contains non-JSON curly braces?**  
A: Will attempt to parse. If invalid, returns with confidence 0.5.

---

## Performance Notes

- **Time:** O(n) where n = text length
- **Space:** O(m) where m = number of JSON fragments
- **Bottleneck:** `json.loads()` parsing, not scanning
- **Optimization:** Not needed for Tier-A (small files)

---

## Related Documentation

- 📘 **Full Implementation Guide:** `docs/EXTRACTOR_JSON_IMPLEMENTATION.md`
- 📊 **Expected Output:** `docs/EXPECTED_OUTPUT.md`
- 🏗️ **Architecture:** `guidelines.md`
- 🧪 **Testing:** `dev_runner.py`

---

## Contact & Questions

If you have questions:
1. Check `docs/EXTRACTOR_JSON_IMPLEMENTATION.md` for details
2. Read code comments in `json_extractor.py`
3. Run `dev_runner.py` to see it in action
4. Ask the team if still unclear

---

## Checklist for Next Developer

When implementing the next extractor:

- [ ] Copy the structure from `json_extractor.py`
- [ ] Extend `BaseExtractor` class
- [ ] Return `List[ExtractedRecord]` with proper `source_type`
- [ ] Add confidence scores
- [ ] Handle edge cases gracefully
- [ ] Update `dev_runner.py` with your extractor
- [ ] Write documentation like this guide
- [ ] Test with `dev_runner.py`

---

**Last Updated:** November 15, 2025  
**Status:** Production Ready ✅  
**Next Module:** `kv_extractor.py`
