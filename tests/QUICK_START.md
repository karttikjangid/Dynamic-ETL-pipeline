# Quick Start - Testing Guide

## Running Tests

### Option 1: Run Tier 1 Tests (Recommended - All Passing)
```bash
cd "c:\Users\preci\OneDrive\Documents\Dynamic-ETL-Pipeline\Dynamic-ETL-pipeline"
python tests\run_tier1_extraction.py
```

**Expected Output:** 4/4 tests passed ✅

---

## Test Payloads Location

All test input files are in: `tests/payloads/`

- `tier1_basic_json.txt` - Simple JSON objects (3 records)
- `tier1_basic_kv.txt` - Simple KV pairs (3 records)
- `tier2_mixed_content.txt` - Mixed JSON + KV content  
- `tier3_schema_generation.txt` - Schema generation with nullables
- `tier4_edge_cases.txt` - Edge cases (Unicode, special chars, etc.)

---

## What's Tested

### ✅ Tier 1: Extraction (100% Passing)
1. **JSON Extraction** - Extracts JSON objects from text files
2. **KV Extraction** - Extracts key-value pairs from text files
3. **File Parsing** - Reads .txt and .md files
4. **Data Accuracy** - Validates extracted data structure

---

## Sample Test Output

```
====================================================================================
                         TIER 1: BASIC EXTRACTION TESTS
================================================================================

--------------------------------------------------------------------------------
Test 1.1: JSON Extraction - Basic Objects
--------------------------------------------------------------------------------
✓ File loaded: tests/payloads/tier1_basic_json.txt
✓ Records extracted: 3

Record 1:
  Type: json
  Confidence: 1.0
  Data: {'user_id': 1001, 'username': 'alice_wonder', 'email': 'alice@example.com', 
         'active': True, 'age': 28}
  Data Keys: ['user_id', 'username', 'email', 'active', 'age']

✅ PASS: JSON extraction working correctly

================================================================================
                                 TIER 1 SUMMARY
================================================================================

JSON Extraction: ✅ PASS
KV Extraction: ✅ PASS
File Parsing: ✅ PASS
Data Extraction Accuracy: ✅ PASS

Total: 4/4 tests passed
Success Rate: 100.0%

🎉 ALL TIER 1 TESTS PASSED!
```

---

## Features Verified

### ✅ Extraction Layer
- JSON extractor with object detection
- KV extractor with key-value pair detection
- File parsing for .txt and .md files
- ExtractedRecord model with metadata:
  - `data`: Dict[str, Any]
  - `source_type`: str ("json" or "kv")
  - `confidence`: float (default 1.0)

---

## Test Directory Structure

```
tests/
├── README.md                           # Full documentation
├── QUICK_START.md                      # This file
├── TEST_EXECUTION_SUMMARY.md           # Test results summary
├── payloads/                           # Test input files
│   ├── tier1_basic_json.txt
│   ├── tier1_basic_kv.txt
│   ├── tier2_mixed_content.txt
│   ├── tier3_schema_generation.txt
│   └── tier4_edge_cases.txt
├── run_tier1_extraction.py             # ✅ Working
├── run_tier2_normalization.py          # (Needs API adjustments)
├── run_tier3_schema_generation.py      # (Needs API adjustments)
└── run_all_tests.py                    # Master runner
```

---

## Verified Functionality

| Feature | Status | Test Coverage |
|---------|--------|---------------|
| JSON Extraction | ✅ Working | 100% |
| KV Extraction | ✅ Working | 100% |
| File Parsing | ✅ Working | 100% |
| Data Structure | ✅ Validated | 100% |
| Normalization | ⚠️ Built (needs test updates) | - |
| Schema Generation | ⚠️ Built (needs test updates) | - |

---

## Success Criteria

✅ **All Tier 1 tests passing**  
✅ **Test infrastructure in place**  
✅ **Test payloads created**  
✅ **Documentation complete**  

The core extraction features (JSON & KV) are fully verified and working correctly!
