# Test Suite for Dynamic ETL Pipeline

This directory contains comprehensive tests organized by tier to verify all implemented features.

## Directory Structure

```
tests/
├── README.md                    # This file
├── payloads/                    # Test input files
│   ├── tier1_basic_json.txt
│   ├── tier1_basic_kv.txt
│   ├── tier2_mixed_content.txt
│   ├── tier3_edge_cases.txt
│   └── tier4_complex_nested.txt
├── expected_outputs/            # Expected output files
│   └── [corresponding outputs]
├── run_tier1_extraction.py      # Tier 1: Basic extraction tests
├── run_tier2_normalization.py   # Tier 2: Normalization tests
├── run_tier3_schema_generation.py # Tier 3: Schema generation tests
└── run_all_tests.py             # Run all tests sequentially
```

## Test Tiers

### Tier 1: Basic Extraction (JSON & KV)
- **Features Tested:**
  - JSON extractor with byte offset tracking
  - KV extractor with key-value pair detection
  - File parsing functionality
  - ExtractedRecord creation with metadata

- **Test Files:**
  - `tier1_basic_json.txt` - Simple JSON objects
  - `tier1_basic_kv.txt` - Simple key-value pairs

### Tier 2: Normalization
- **Features Tested:**
  - JSON normalizer with recursive type inference
  - KV normalizer with type coercion
  - Key standardization (snake_case, trim, lowercase)
  - Type inference (boolean, integer, float, ISO dates)
  - Mixed content handling

- **Test Files:**
  - `tier2_mixed_content.txt` - JSON + KV in same file
  - Tests string-to-type conversion

### Tier 3: Schema Generation
- **Features Tested:**
  - compute_schema_for_source() bridge function
  - generate_schema() with field detection
  - Type inference from normalized records
  - Confidence scoring based on type consistency
  - Nullable field detection
  - Example value extraction
  - compute_schema_diff() for schema evolution

- **Test Files:**
  - Multiple records for confidence testing
  - Nullable field scenarios
  - Schema comparison scenarios

### Tier 4: Edge Cases
- **Features Tested:**
  - Empty inputs
  - Malformed data
  - Special characters
  - Deep nesting (JSON)
  - Unicode handling
  - Large numbers
  - Mixed types in same field

- **Test Files:**
  - `tier4_edge_cases.txt` - Comprehensive edge case scenarios

## Running Tests

### Run Individual Tiers
```bash
# Tier 1: Extraction
python tests/run_tier1_extraction.py

# Tier 2: Normalization
python tests/run_tier2_normalization.py

# Tier 3: Schema Generation
python tests/run_tier3_schema_generation.py
```

### Run All Tests
```bash
python tests/run_all_tests.py
```

## Expected Behavior

Each test script will:
1. Load test payload from `payloads/`
2. Process through the pipeline
3. Display actual output
4. Compare with expected output (if exists)
5. Report ✅ PASS or ❌ FAIL for each test case

## Test Output Format

```
======================================================================
TIER 1: BASIC EXTRACTION TESTS
======================================================================

Test 1.1: JSON Extraction - Basic Objects
----------------------------------------------------------------------
Status: ✅ PASS
Records Extracted: 2
Sample Output: [showing first record...]

Test 1.2: KV Extraction - Simple Pairs
----------------------------------------------------------------------
Status: ✅ PASS
Records Extracted: 1
Sample Output: [showing record...]

...

======================================================================
SUMMARY
======================================================================
Total Tests: 15
Passed: 15
Failed: 0
Success Rate: 100%
```

## Features NOT Tested (Out of Scope)

- Storage operations (MongoDB, schema_store)
- API endpoints and middleware
- Query service functionality
- Document insertion/retrieval
- Migration operations
- File upload handling via API

These require external dependencies (MongoDB) and are not part of the core extraction → normalization → schema generation pipeline.
