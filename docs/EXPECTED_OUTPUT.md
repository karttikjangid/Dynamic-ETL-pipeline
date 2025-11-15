# Expected Output from dev_runner.py

When you run:
```bash
python dev_runner.py
```

You should see output similar to this:

```
============================================================
Testing JSON Extractor
============================================================

JSON Records Found: 1

1. JSON Record:
   Confidence: 1.0
   Data: {'id': '123', 'name': 'Sample Item', 'details': {'color': 'blue'}}

============================================================
Testing Key-Value Extractor
============================================================

Key-Value Records Found: 0

============================================================
Combined Results
============================================================

Total Records Extracted: 1
  - JSON fragments: 1
  - KV pairs: 0
```

---

## Detailed Breakdown

### JSON Extractor Results
The JSON extractor found **1 fragment**:
- **Source Type:** json
- **Confidence:** 1.0 (successfully parsed)
- **Data Structure:**
  ```python
  {
      'id': '123',
      'name': 'Sample Item',
      'details': {
          'color': 'blue'
      }
  }
  ```

### Key-Value Extractor Results
Currently shows **0 records** because `kv_extractor.py` is not yet implemented.

Once implemented, it should extract:
```python
{
    'title': 'Widget A',
    'price': 9.99
}
```

---

## Running the Test

### Step 1: Ensure you're in the project root
```bash
cd c:\Users\preci\OneDrive\Documents\Dynamic-ETL-Pipeline\Dynamic-ETL-pipeline
```

### Step 2: Run the dev script
```bash
python dev_runner.py
```

### Expected Behavior
- ✅ JSON extractor works and finds 1 JSON object
- ⚠️ KV extractor shows error (NotImplementedError) - this is expected
- 📊 Summary shows total extraction statistics

---

## What to Look For

### Success Indicators
1. **No exceptions** from JSON extractor
2. **Confidence = 1.0** for valid JSON
3. **Proper nested structure** in details.color
4. **Correct data types** (strings, not raw text)

### Potential Issues
1. **If confidence = 0.5:** JSON parsing failed, check the raw data
2. **If 0 records found:** Check if brackets are balanced in test data
3. **If multiple records:** May have found multiple JSON fragments

---

## Testing Different Scenarios

### Test 1: Multiple JSON Objects
Modify `dev_runner.py`:
```python
text = """
{ "id": "1", "name": "First" }
{ "id": "2", "name": "Second" }
"""
```

**Expected:** 2 JSON records found

---

### Test 2: Malformed JSON
```python
text = """
{ "id": "123", broken syntax }
"""
```

**Expected:** 1 record with confidence = 0.5, contains `_parse_error`

---

### Test 3: Nested Complex JSON
```python
text = """
{
  "user": {
    "profile": {
      "settings": {
        "theme": "dark"
      }
    }
  }
}
"""
```

**Expected:** 1 record with deeply nested structure preserved

---

### Test 4: JSON with Trailing Comma
```python
text = """
{ "id": "123", "name": "test", }
"""
```

**Expected:** 1 record with confidence = 1.0 (auto-fixed)

---

## Production Output Example

When integrated with the full pipeline (`POST /upload`), the response will look like:

```json
{
  "status": "success",
  "source_id": "file_abc123",
  "file_id": "upload_xyz789",
  "schema_id": "file_abc123_v1",
  "records_extracted": 1,
  "records_normalized": 1,
  "parsed_fragments_summary": {
    "json_fragments": 1,
    "kv_pairs": 2
  }
}
```

The `parsed_fragments_summary` shows:
- **json_fragments: 1** - Our JSON object
- **kv_pairs: 2** - The title and price (when KV extractor implemented)

---

## Debugging Tips

### If output is unexpected:

1. **Check imports:** Ensure `core.models` is accessible
2. **Print intermediate:** Add `print(fragments)` in extract() method
3. **Test parse_json_string directly:**
   ```python
   from extractors.json_extractor import parse_json_string
   result = parse_json_string('{"id": 1}')
   print(result)
   ```
4. **Check text encoding:** Ensure no hidden characters in test string

### Common Errors

**ModuleNotFoundError: No module named 'core'**
- Solution: Run from project root, not inside extractors/

**NotImplementedError from KVExtractor**
- Solution: Expected! KV extractor not yet implemented

**AttributeError: 'dict' object has no attribute 'data'**
- Solution: Check that ExtractedRecord is properly imported

---

## Next Steps

After confirming JSON extractor works:

1. ✅ Implement `kv_extractor.py` (key-value extraction)
2. ✅ Implement `file_parser.py` (file reading)
3. ✅ Implement `orchestrator.py` (combines extractors)
4. ✅ Test with real `.txt` and `.md` files
5. ✅ Connect to normalizer layer

---

## Summary

The output demonstrates that:
- JSON extraction is working correctly
- Nested objects are preserved
- Confidence scoring is applied
- ExtractedRecord models are created properly
- Ready for integration with normalizers

Your teammates can use this as a reference to understand what successful extraction looks like!
