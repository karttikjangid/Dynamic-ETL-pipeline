# Visual Guide: JSON Extractor Output Flow

## Input → Processing → Output

```
┌──────────────────────────────────────────────────────────┐
│                      INPUT TEXT                          │
│                                                          │
│  title: Widget A                                         │
│  price: 9.99                                             │
│                                                          │
│  { "id": "123", "name": "Sample Item",                  │
│    "details": {"color": "blue"} }                       │
│                                                          │
└──────────────────────────────────────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────────────┐
│            JSONExtractor().extract(text)                 │
│                                                          │
│  Step 1: Scan for opening brace {                       │
│  Step 2: Track nested braces with stack                 │
│  Step 3: Find balanced closing }                        │
│  Step 4: Extract raw JSON string                        │
│  Step 5: Parse with json.loads()                        │
│  Step 6: Create ExtractedRecord                         │
│                                                          │
└──────────────────────────────────────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────────────┐
│                  OUTPUT RECORDS                          │
│                                                          │
│  [                                                       │
│    ExtractedRecord(                                      │
│      data={                                              │
│        "id": "123",                                      │
│        "name": "Sample Item",                            │
│        "details": {                                      │
│          "color": "blue"                                 │
│        }                                                 │
│      },                                                  │
│      source_type="json",                                 │
│      confidence=1.0                                      │
│    )                                                     │
│  ]                                                       │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## Detailed Processing Steps

### Step 1: Text Scanning
```
Input: "title: Widget A\nprice: 9.99\n\n{ \"id\": \"123\" }"
        ↓
Scanner: Looking for '{'
        ↓
Found at position 30: { "id": "123" }
```

### Step 2: Bracket Balancing
```
Position 30: { ← Stack: ['{']
Position 31: "
Position 35: "
Position 36: : ← Still in object, stack: ['{']
...
Position 43: } ← Stack: [] (empty = balanced!)
```

### Step 3: Extraction
```
Extract substring from position 30 to 44:
{ "id": "123", "name": "Sample Item", "details": {"color": "blue"} }
```

### Step 4: Parsing
```
json.loads('{ "id": "123", ... }')
        ↓
{
  "id": "123",
  "name": "Sample Item",
  "details": {
    "color": "blue"
  }
}
```

### Step 5: Record Creation
```
ExtractedRecord(
  data={parsed_dict},
  source_type="json",
  confidence=1.0
)
```

---

## Running dev_runner.py - Visual Output

```
$ python dev_runner.py

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
Traceback (most recent call last):
  ...
NotImplementedError

[This is expected - KV extractor not yet implemented]
```

---

## Production API Response Format

When integrated into the full pipeline:

```json
POST /upload
Response:
{
  "status": "success",
  "source_id": "file_20251115_abc123",
  "file_id": "upload_xyz789",
  "schema_id": "file_20251115_abc123_v1",
  "records_extracted": 1,
  "records_normalized": 1,
  "parsed_fragments_summary": {
    "json_fragments": 1,      ← Our JSON object
    "kv_pairs": 2             ← title and price (when KV extractor done)
  }
}
```

---

## Data Flow Through Pipeline

```
┌─────────────┐
│  Input File │
│  data.txt   │
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│  File Content       │
│  (raw text string)  │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  JSONExtractor      │
│  .extract()         │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│  List[ExtractedRecord]              │
│  [                                  │
│    ExtractedRecord(                 │
│      data={'id': '123', ...},       │
│      source_type='json',            │
│      confidence=1.0                 │
│    )                                │
│  ]                                  │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────┐
│  JSON Normalizer    │ ← Next step
│  (cleans data)      │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  Schema Generator   │
│  (infers types)     │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  MongoDB Storage    │
└─────────────────────┘
```

---

## Confidence Score Decision Tree

```
Extract JSON Fragment
        │
        ▼
   Parse with json.loads()
        │
        ├─── Success? ──→ confidence = 1.0
        │                      │
        │                      ▼
        │              Create Record with
        │              parsed data dict
        │
        └─── Fail?
                │
                ▼
        Try auto-fixes:
        - Remove trailing commas
        - Replace single quotes
                │
                ├─── Success? ──→ confidence = 1.0
                │
                └─── Still Fail? ──→ confidence = 0.5
                                          │
                                          ▼
                                    Create Record with
                                    metadata + raw string
```

---

## Record Structure Comparison

### Successful Parse (confidence = 1.0)
```python
ExtractedRecord(
    data={
        "id": "123",              # ← Actual parsed data
        "name": "Sample Item",
        "details": {
            "color": "blue"
        }
    },
    source_type="json",
    confidence=1.0                # ← High confidence
)
```

### Failed Parse (confidence = 0.5)
```python
ExtractedRecord(
    data={
        "_raw": "{ broken json }",     # ← Original text
        "_parse_error": True,           # ← Error flag
        "chunk_id": "json_1",          # ← Fragment ID
        "start": 0,                    # ← Position info
        "end": 16
    },
    source_type="json",
    confidence=0.5                     # ← Low confidence
)
```

---

## Multiple Fragments Example

### Input
```
First JSON: { "id": 1, "type": "user" }
Some text in between...
Second JSON: { "id": 2, "type": "admin" }
```

### Output
```python
[
    ExtractedRecord(
        data={"id": 1, "type": "user"},
        source_type="json",
        confidence=1.0
    ),
    ExtractedRecord(
        data={"id": 2, "type": "admin"},
        source_type="json",
        confidence=1.0
    )
]
```

### Visual Representation
```
Records[0] ──→ { "id": 1, "type": "user" }
Records[1] ──→ { "id": 2, "type": "admin" }

Both have confidence = 1.0
Both have source_type = "json"
```

---

## Edge Cases Handled

### Case 1: Nested JSON
```
Input:  { "a": { "b": { "c": 1 } } }
Output: Single record with nested structure preserved
```

### Case 2: JSON in Sentence
```
Input:  "The config is { "active": true } for now"
Output: Single record with {"active": true}
```

### Case 3: Empty Object
```
Input:  { }
Output: Single record with {} (empty dict)
```

### Case 4: String with Braces
```
Input:  { "text": "hello {world}" }
Output: Correctly parsed, braces in string ignored
```

### Case 5: Multiple Objects
```
Input:  { "a": 1 } { "b": 2 }
Output: Two separate records
```

---

## Testing Checklist Output

When you run tests, verify:

✅ **Basic Extraction**
```
Input:  { "id": 1 }
Output: 1 record, confidence=1.0, data={"id": 1}
```

✅ **Nested Objects**
```
Input:  { "user": { "name": "test" } }
Output: 1 record, nested structure intact
```

✅ **Multiple Fragments**
```
Input:  { "a": 1 } and { "b": 2 }
Output: 2 records
```

✅ **Auto-Fix Trailing Comma**
```
Input:  { "id": 1, }
Output: 1 record, confidence=1.0 (fixed)
```

✅ **Failed Parse**
```
Input:  { invalid }
Output: 1 record, confidence=0.5, contains _parse_error
```

---

## Summary Visualization

```
┌─────────────────────────────────────────────────────┐
│                 JSON EXTRACTOR                      │
│                                                     │
│  Input:  Raw text with JSON objects                │
│  Output: List[ExtractedRecord]                     │
│                                                     │
│  Features:                                          │
│  • Stack-based bracket scanning                    │
│  • Auto-fixes common issues                        │
│  • Confidence scoring                              │
│  • Handles nested structures                       │
│  • Multiple fragments support                      │
│                                                     │
│  Status: ✅ Production Ready                       │
└─────────────────────────────────────────────────────┘
```

---

**Use this guide to understand what the extractor produces at each stage!**
