# Normalization Guide

**Dynamic ETL Pipeline - Data Normalization Layer**

> Last Updated: November 15, 2025  
> Version: 1.0

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [KV Normalizer](#kv-normalizer)
4. [JSON Normalizer](#json-normalizer)
5. [Type Inference](#type-inference)
6. [Key Standardization](#key-standardization)
7. [Usage Examples](#usage-examples)
8. [Best Practices](#best-practices)

---

## Overview

The **Normalization Layer** transforms raw extracted data into clean, typed, and standardized records ready for schema inference and storage. This layer sits between extraction and schema detection in the ETL pipeline.

### Pipeline Flow

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Extractors  │ ──> │  Normalizers │ ──> │   Schema     │
│              │     │              │     │  Inference   │
│ JSON/KV Data │     │ Type & Clean │     │  & Storage   │
└──────────────┘     └──────────────┘     └──────────────┘
```

### Key Responsibilities

- **Type Inference**: Convert string values to appropriate Python types
- **Key Standardization**: Normalize key names to consistent format
- **Data Cleaning**: Handle null values, empty strings, edge cases
- **Deterministic Output**: Same input always produces same output
- **No External Dependencies**: Uses only Python stdlib

---

## Architecture

### Base Normalizer

All normalizers inherit from `BaseNormalizer`:

```python
from normalizers.base import BaseNormalizer

class BaseNormalizer(ABC):
    @abstractmethod
    def normalize(self, records: List[Dict]) -> List[NormalizedRecord]:
        pass
```

### Normalizer Types

| Normalizer | Input | Output | Purpose |
|------------|-------|--------|---------|
| `KVNormalizer` | KV records | `NormalizedRecord` | Type inference for key-value pairs |
| `JSONNormalizer` | JSON records | `NormalizedRecord` | Clean and standardize JSON data |

---

## KV Normalizer

### Purpose

Transforms key-value pairs (extracted as strings) into properly-typed Python objects.

### Class: `KVNormalizer`

**Location**: `normalizers/kv_normalizer.py`

#### Method: `normalize()`

```python
def normalize(self, records: List[Dict]) -> List[NormalizedRecord]:
    """
    Normalize list of KV records into NormalizedRecord objects.
    
    Args:
        records: List of dicts with 'data', 'source_type', 'confidence' keys
        
    Returns:
        List of NormalizedRecord objects with normalized data
    """
```

**Input Format**:
```python
[
    {
        "data": {"price": "9.99", "status": "active"},
        "source_type": "kv",
        "confidence": 1.0
    }
]
```

**Output Format**:
```python
[
    NormalizedRecord(
        data={"price": 9.99, "status": "active"},
        original_source="kv",
        extraction_confidence=1.0
    )
]
```

---

## JSON Normalizer

### Purpose

Normalizes JSON objects by recursively applying type inference to string values while preserving the exact JSON structure.

### Class: `JSONNormalizer`

**Location**: `normalizers/json_normalizer.py`

#### Method: `normalize()`

```python
def normalize(self, records: List[Dict]) -> List[NormalizedRecord]:
    """
    Normalize list of JSON records into NormalizedRecord objects.
    
    Args:
        records: List of dicts with 'data', 'source_type', 'confidence' keys
        
    Returns:
        List of NormalizedRecord objects with normalized data
    """
```

**Input Format**:
```python
[
    {
        "data": {
            "product_id": "P-123",
            "price": "299.99",
            "available": "true",
            "specs": {
                "weight": "45"
            }
        },
        "source_type": "json",
        "confidence": 1.0
    }
]
```

**Output Format**:
```python
[
    NormalizedRecord(
        data={
            "product_id": "P-123",
            "price": 299.99,
            "available": True,
            "specs": {
                "weight": 45
            }
        },
        original_source="json",
        extraction_confidence=1.0
    )
]
```

### Key Differences from KV Normalizer

| Feature | JSON Normalizer | KV Normalizer |
|---------|----------------|---------------|
| **Key Standardization** | ❌ Not applied (preserves original keys) | ✅ Applied (converts to snake_case) |
| **Type Inference** | ✅ Applied to string values | ✅ Applied to all values |
| **Shape Preservation** | ✅ Exact structure preserved | ✅ Flat structure maintained |
| **Already-typed values** | ✅ Kept as-is (int, bool, etc.) | N/A (all KV values are strings) |

### Function: `normalize_json_record()`

```python
def normalize_json_record(record: Dict) -> Optional[Dict]:
    """
    Normalize a single JSON record.
    
    Recursively processes the JSON structure, applying type inference
    to string values while preserving the overall shape.
    """
```

### Function: `clean_json_values()`

```python
def clean_json_values(value: Any) -> Any:
    """
    Recursively normalize JSON values.
    
    Handles:
    - Dicts: recurse on all values
    - Lists: recurse on all elements
    - Strings: apply type inference
    - Booleans: keep as-is
    - Numbers: keep as-is
    - None: keep as-is
    """
```

### Examples

#### Example 1: Simple JSON Object

**Input**:
```python
{
    "name": "Product",
    "price": "99.99",
    "quantity": "10",
    "available": "true"
}
```

**Output**:
```python
{
    "name": "Product",
    "price": 99.99,
    "quantity": 10,
    "available": True
}
```

#### Example 2: Nested JSON Structure

**Input**:
```python
{
    "product": {
        "id": "P-123",
        "details": {
            "price": "149.99",
            "stock": "25"
        }
    }
}
```

**Output**:
```python
{
    "product": {
        "id": "P-123",
        "details": {
            "price": 149.99,
            "stock": 25
        }
    }
}
```

Note: Structure is **exactly preserved** - same keys, same nesting.

#### Example 3: Arrays in JSON

**Input**:
```python
{
    "items": [
        {"id": "1", "price": "10.99"},
        {"id": "2", "price": "20.99"}
    ],
    "counts": ["10", "20", "30"]
}
```

**Output**:
```python
{
    "items": [
        {"id": 1, "price": 10.99},
        {"id": 2, "price": 20.99}
    ],
    "counts": [10, 20, 30]
}
```

#### Example 4: Mixed Already-Typed Values

**Input**:
```python
{
    "id": 12345,           # Already int
    "name": "Test",        # Already string
    "active": True,        # Already bool
    "price": "99.99",      # String → will convert
    "count": "50"          # String → will convert
}
```

**Output**:
```python
{
    "id": 12345,           # Preserved
    "name": "Test",        # Preserved
    "active": True,        # Preserved
    "price": 99.99,        # Converted
    "count": 50            # Converted
}
```

### Shape Preservation Guarantee

The JSON normalizer **guarantees** that:
1. All keys remain in the same order
2. Nested structures maintain exact depth
3. Arrays maintain exact length and order
4. Only string values undergo type inference
5. Already-typed values (int, float, bool, None) are untouched

---

## Type Inference

### Function: `infer_value_type(value: str) -> Any`

Automatically detects and converts string values to appropriate Python types.

### Conversion Rules

| Input Type | Pattern | Output | Example |
|------------|---------|--------|---------|
| **Boolean** | `"true"` (case-insensitive) | `True` | `"true"` → `True` |
| **Boolean** | `"false"` (case-insensitive) | `False` | `"False"` → `False` |
| **Integer** | Digits only, no decimal | `int` | `"42"` → `42` |
| **Float** | Contains decimal point | `float` | `"3.14"` → `3.14` |
| **Null** | `"null"`, `"none"`, `"-"`, `"n/a"` | `None` | `"null"` → `None` |
| **ISO Date** | `YYYY-MM-DD` | `str` (kept) | `"2025-11-15"` → `"2025-11-15"` |
| **ISO DateTime** | `YYYY-MM-DDTHH:MM:SS` | `str` (kept) | `"2025-11-15T10:30:00"` → kept |
| **String** | Everything else | `str` | `"hello"` → `"hello"` |

### Examples

#### Boolean Conversion
```python
infer_value_type("true")   # → True
infer_value_type("TRUE")   # → True
infer_value_type("false")  # → False
infer_value_type("False")  # → False
```

#### Numeric Conversion
```python
infer_value_type("42")     # → 42 (int)
infer_value_type("3.14")   # → 3.14 (float)
infer_value_type("0")      # → 0 (int)
infer_value_type("-273")   # → -273 (int)
infer_value_type("1.5e2")  # → 150.0 (float)
```

#### Null Handling
```python
infer_value_type("null")   # → None
infer_value_type("NULL")   # → None
infer_value_type("none")   # → None
infer_value_type("None")   # → None
infer_value_type("-")      # → None
infer_value_type("n/a")    # → None
infer_value_type("N/A")    # → None
infer_value_type("na")     # → None
```

#### Date Preservation
```python
infer_value_type("2025-11-15")             # → "2025-11-15" (kept as string)
infer_value_type("2025-11-15T10:30:00")    # → kept as string
infer_value_type("2025-11-15T10:30:00Z")   # → kept as string
infer_value_type("2025-11-15T10:30:00.123Z") # → kept as string
```

#### String Preservation
```python
infer_value_type("hello")        # → "hello"
infer_value_type("SW-123-ABC")   # → "SW-123-ABC"
infer_value_type("")             # → ""
infer_value_type("  ")           # → "" (trimmed)
```

### Recursive Type Inference

The function handles nested structures:

```python
# Nested dictionary
infer_value_type({
    "count": "42",
    "price": "9.99"
})
# → {"count": 42, "price": 9.99}

# Nested list
infer_value_type(["42", "3.14", "true"])
# → [42, 3.14, True]
```

---

## Key Standardization

### Function: `standardize_key_names(record: Dict) -> Dict`

Converts dictionary keys to a consistent, deterministic format.

### Standardization Rules

1. **Convert to lowercase**: `ProductName` → `productname`
2. **Replace spaces with underscores**: `product name` → `product_name`
3. **Replace hyphens with underscores**: `product-name` → `product_name`
4. **Remove special characters**: `price!@#` → `price`
5. **Collapse multiple underscores**: `key___name` → `key_name`
6. **Strip leading/trailing underscores**: `_key_` → `key`
7. **Fallback for empty keys**: `""` → `unknown`

### Examples

```python
# Case normalization
_standardize_key("ProductName")      # → "productname"
_standardize_key("PRODUCT_NAME")     # → "product_name"

# Space and hyphen replacement
_standardize_key("product name")     # → "product_name"
_standardize_key("product-name")     # → "product_name"
_standardize_key("product name-id")  # → "product_name_id"

# Special character removal
_standardize_key("price$")           # → "price"
_standardize_key("user@email")       # → "useremail"
_standardize_key("key!@#$%")         # → "key"

# Multiple underscores
_standardize_key("key___name")       # → "key_name"
_standardize_key("__private__")      # → "private"

# Edge cases
_standardize_key("_internal")        # → "internal"
_standardize_key("key_")             # → "key"
_standardize_key("")                 # → "unknown"
_standardize_key("123")              # → "123"
```

---

## Usage Examples

### Example 1: Basic KV Normalization

```python
from normalizers.kv_normalizer import KVNormalizer

# Input from KV extractor
records = [
    {
        "data": {
            "product-name": "Smart Watch",
            "price": "299.99",
            "in_stock": "true",
            "quantity": "150",
            "discount": "null"
        },
        "source_type": "kv",
        "confidence": 1.0
    }
]

# Normalize
normalizer = KVNormalizer()
normalized = normalizer.normalize(records)

# Output
print(normalized[0].data)
# {
#     "product_name": "Smart Watch",
#     "price": 299.99,
#     "in_stock": True,
#     "quantity": 150,
#     "discount": None
# }
```

### Example 2: Complex Data

```python
records = [
    {
        "data": {
            "Product ID": "SW-2025-001",
            "release-date": "2025-01-15",
            "Price (USD)": "149.99",
            "Available": "TRUE",
            "Stock Count": "42",
            "Rating": "4.7",
            "Discontinued": "false",
            "Notes": "-"
        },
        "source_type": "kv",
        "confidence": 1.0
    }
]

normalized = KVNormalizer().normalize(records)

print(normalized[0].data)
# {
#     "product_id": "SW-2025-001",
#     "release_date": "2025-01-15",  # Date kept as string
#     "price_usd": 149.99,            # Float conversion
#     "available": True,              # Boolean conversion
#     "stock_count": 42,              # Integer conversion
#     "rating": 4.7,                  # Float conversion
#     "discontinued": False,          # Boolean conversion
#     "notes": None                   # Null conversion
# }
```

### Example 3: Edge Cases

```python
records = [
    {
        "data": {
            "empty": "",
            "whitespace": "   ",
            "zero": "0",
            "negative": "-42",
            "scientific": "1.5e2",
            "iso_datetime": "2025-11-15T10:30:00Z",
            "not_a_number": "N/A",
            "__private__key": "secret"
        },
        "source_type": "kv",
        "confidence": 1.0
    }
]

normalized = KVNormalizer().normalize(records)

print(normalized[0].data)
# {
#     "empty": "",                              # Empty string preserved
#     "whitespace": "",                         # Trimmed to empty
#     "zero": 0,                                # Integer zero
#     "negative": -42,                          # Negative integer
#     "scientific": 150.0,                      # Scientific notation
#     "iso_datetime": "2025-11-15T10:30:00Z",  # ISO datetime preserved
#     "not_a_number": None,                     # N/A → None
#     "private_key": "secret"                   # Key standardized
# }
```

---

## Best Practices

### 1. Always Normalize Before Schema Inference

```python
# ✅ CORRECT
records = extractor.extract(content)
normalized = normalizer.normalize(records)
schema = schema_detector.infer(normalized)

# ❌ INCORRECT - Skip normalization
records = extractor.extract(content)
schema = schema_detector.infer(records)  # Types will be wrong!
```

### 2. Handle Empty Results

```python
normalized = normalizer.normalize(records)

if not normalized:
    logger.warning("No records after normalization")
    return []
```

### 3. Preserve Original Data

```python
# Original data is preserved in ExtractedRecord
# Normalized data is in NormalizedRecord

for norm_rec in normalized:
    print(f"Source: {norm_rec.original_source}")
    print(f"Confidence: {norm_rec.extraction_confidence}")
    print(f"Data: {norm_rec.data}")
```

### 4. Test Edge Cases

Always test with:
- Empty strings
- Whitespace-only values
- Null-like values (`null`, `none`, `N/A`, `-`)
- Boolean strings (`true`, `false`, case variations)
- Numeric strings (integers, floats, scientific notation)
- ISO dates and datetimes
- Special characters in keys
- Unicode characters

### 5. Deterministic Output

Normalization is deterministic - same input always produces same output:

```python
# These will always produce identical results
result1 = normalizer.normalize(records)
result2 = normalizer.normalize(records)

assert result1[0].data == result2[0].data  # Always True
```

---

## Implementation Details

### Algorithm Complexity

- **Key Standardization**: O(k) where k = key length
- **Type Inference**: O(v) where v = value length
- **Record Normalization**: O(n × m) where n = records, m = avg fields per record

### Performance Characteristics

- **No External Dependencies**: Pure Python stdlib (fast, no I/O)
- **Memory Efficient**: Processes records one at a time
- **Deterministic**: No random behavior, consistent output
- **Thread-Safe**: No shared mutable state

### Design Decisions

#### Why Keep ISO Dates as Strings?

**Reason**: Avoid timezone ambiguity and parsing complexity.

```python
# ✅ Keep as string - no ambiguity
"2025-11-15" → "2025-11-15"

# ❌ Parse to datetime - which timezone?
"2025-11-15" → datetime(2025, 11, 15, tzinfo=?)
```

Later stages (schema inference, storage) can handle timezone-aware parsing if needed.

#### Why No Fuzzy Date Parsing?

**Reason**: Prevent false positives and maintain determinism.

```python
# Fuzzy parsing can misinterpret:
"10-12-2025"  # US: Oct 12 or UK: Dec 10?
"next monday" # Depends on when code runs!
"Q4 2025"     # Ambiguous format

# Strict ISO only:
"2025-11-15"  # ✅ Unambiguous
"2025-11-15T10:30:00Z"  # ✅ Unambiguous
```

#### Why Standardize Keys?

**Reason**: Enable deterministic schema detection and prevent duplicates.

```python
# Without standardization - duplicates!
{
    "Product-Name": "Widget",
    "product_name": "Widget",
    "PRODUCT_NAME": "Widget"
}

# After standardization - single key
{
    "product_name": "Widget"
}
```

---

## Testing

### Unit Tests

```python
from normalizers.kv_normalizer import infer_value_type, _standardize_key

# Test type inference
assert infer_value_type("42") == 42
assert infer_value_type("3.14") == 3.14
assert infer_value_type("true") == True
assert infer_value_type("null") == None
assert infer_value_type("2025-11-15") == "2025-11-15"

# Test key standardization
assert _standardize_key("Product Name") == "product_name"
assert _standardize_key("price$") == "price"
assert _standardize_key("__private__") == "private"
```

### Integration Test

```python
def test_kv_normalization_pipeline():
    # Extract
    extractor = KVExtractor()
    records = extractor.extract(test_content)
    
    # Normalize
    normalizer = KVNormalizer()
    normalized = normalizer.normalize([r.dict() for r in records])
    
    # Verify
    assert len(normalized) > 0
    assert all(isinstance(r, NormalizedRecord) for r in normalized)
    assert all(r.extraction_confidence > 0 for r in normalized)
```

---

## Future Enhancements

### Planned Features

1. **Custom Type Mappings**: Allow user-defined type conversions
2. **Validation Rules**: Add field-level validation (min/max, patterns)
3. **Error Recovery**: Collect and report normalization errors
4. **Performance Metrics**: Track normalization time and success rates

### Not Planned

- ❌ Fuzzy date parsing (too error-prone)
- ❌ Machine learning for type detection (determinism required)
- ❌ External API calls (no network dependencies)
- ❌ Database-specific formatting (handled by storage layer)

---

## Troubleshooting

### Issue: Numbers Staying as Strings

**Problem**: `"42"` not converting to `42`

**Solution**: Check for whitespace or special characters

```python
# ❌ Won't convert
infer_value_type("42 ")  # Has trailing space
infer_value_type("$42")  # Has currency symbol

# ✅ Will convert
infer_value_type("42")
infer_value_type("42".strip())
```

### Issue: Keys Not Standardizing

**Problem**: Keys like `"Product Name"` not converting

**Solution**: Use `standardize_key_names()` or ensure `normalize_kv_record()` is called

```python
# ✅ Automatic standardization
record = {"Product Name": "Widget"}
normalized = normalize_kv_record(record)
# → {"product_name": "Widget"}
```

### Issue: Dates Being Converted to Strings

**Problem**: User expects datetime objects

**Solution**: This is by design! Parse dates in later stages if needed.

```python
# Normalization: Keep as string
normalized_value = infer_value_type("2025-11-15")  # → "2025-11-15"

# Schema inference or storage: Convert if needed
from datetime import datetime
parsed_date = datetime.fromisoformat(normalized_value)
```

---

## API Reference

### Classes

#### `KVNormalizer`

```python
class KVNormalizer(BaseNormalizer):
    def normalize(self, records: List[Dict]) -> List[NormalizedRecord]:
        """Normalize KV records into typed NormalizedRecord objects."""
```

### Functions

#### `normalize_kv_record()`

```python
def normalize_kv_record(record: Dict[str, str]) -> Optional[Dict]:
    """
    Normalize a single KV record.
    
    Args:
        record: Dict with string keys and values
        
    Returns:
        Normalized dict with typed values, or None if empty
    """
```

#### `infer_value_type()`

```python
def infer_value_type(value: str) -> Any:
    """
    Infer and convert string value to appropriate type.
    
    Args:
        value: String value to type-infer
        
    Returns:
        Typed value (bool, int, float, None, or str)
    """
```

#### `standardize_key_names()`

```python
def standardize_key_names(record: Dict) -> Dict:
    """
    Standardize all keys in a record.
    
    Args:
        record: Dict with potentially inconsistent keys
        
    Returns:
        Dict with standardized keys
    """
```

---

## Appendix

### Complete Type Conversion Table

| Input | Type | Output | Notes |
|-------|------|--------|-------|
| `"true"` | bool | `True` | Case-insensitive |
| `"false"` | bool | `False` | Case-insensitive |
| `"42"` | int | `42` | Integers only |
| `"3.14"` | float | `3.14` | Decimal numbers |
| `"null"` | None | `None` | Null literals |
| `"none"` | None | `None` | Python None |
| `"-"` | None | `None` | Dash as null |
| `"n/a"` | None | `None` | Not available |
| `"2025-11-15"` | str | `"2025-11-15"` | ISO date |
| `"2025-11-15T10:30:00"` | str | `"2025-11-15T10:30:00"` | ISO datetime |
| `""` | str | `""` | Empty string |
| `"hello"` | str | `"hello"` | Regular string |

### Version History

- **v1.0** (2025-11-15): Initial implementation of KV normalizer

---

**End of Normalization Guide**
